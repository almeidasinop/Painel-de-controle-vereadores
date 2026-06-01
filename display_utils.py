"""
Utilitários para posicionar a tela do público/plenário em monitores.
"""

from __future__ import annotations

import sys
from typing import List, Optional, Tuple

import re

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontMetrics, QScreen
from PySide6.QtWidgets import QApplication, QLabel, QWidget


def normalize_session_title_line(text: str) -> str:
    """Garante título em uma única linha (sem quebras)."""
    if not text:
        return ""
    line = str(text).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", line).strip()


# Margem horizontal total (esq + dir) ao preencher a largura disponível.
FILL_WIDTH_EDGE_MARGIN_PX = 12

# Folga anti-corte (diferença métrica × renderização no QLabel).
_CLIP_GUARD_PX = 3


def _session_title_font(size_px: int) -> QFont:
    font = QFont("Arial Black")
    font.setPixelSize(size_px)
    font.setWeight(QFont.Weight.Black)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


def _text_render_width(fm: QFontMetrics, text: str) -> int:
    adv = fm.horizontalAdvance(text)
    tight = fm.boundingRect(text).width()
    return max(adv, tight)


def safe_content_width(
    max_width_px: int,
    extra_pad_x: int = 0,
    *,
    edge_margin_px: int = FILL_WIDTH_EDGE_MARGIN_PX,
) -> int:
    """Largura útil para o texto (largura do widget − margens)."""
    raw = max(40, int(max_width_px) - int(extra_pad_x))
    return max(40, raw - int(edge_margin_px))


def effective_label_content_width(label: QLabel, fallback_width: int) -> int:
    """Largura do QLabel após layout (ou fallback antes do primeiro paint)."""
    w = label.width()
    if w <= 0:
        w = int(fallback_width)
    m = label.contentsMargins()
    return max(40, w - m.left() - m.right())


def _estimate_font_high_bound(text: str, target_width_px: int, cap_px: int) -> int:
    """Limite superior para busca: fonte grande o suficiente para preencher a linha."""
    n = max(len(text), 1)
    # Arial Black ≈ 0,55–0,62 × fontSize por caractere (maiúsculas).
    by_chars = int(target_width_px / (n * 0.52))
    by_width = int(target_width_px * 0.85)
    return max(24, cap_px, by_chars, by_width)


def _largest_font_that_fits(text: str, target_width_px: int, font_high: int) -> int:
    """Maior fonte (px) em que o texto cabe em target_width_px (preenche a largura)."""
    limit = target_width_px - _CLIP_GUARD_PX
    low, high = 12, max(12, int(font_high))
    best = 12

    while low <= high:
        mid = (low + high) // 2
        fm = QFontMetrics(_session_title_font(mid))
        if _text_render_width(fm, text) <= limit:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    return best


def apply_single_line_adaptive_text(
    label: QLabel,
    text: str,
    max_font_px: int,
    max_width_px: int,
    *,
    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
    extra_pad_x: int = 0,
    extra_css: str = "",
    fill_width: bool = True,
    edge_margin_px: int = FILL_WIDTH_EDGE_MARGIN_PX,
) -> int:
    """
    Uma linha: maior fonte possível que caiba na largura (preenche a área útil).
    Retorna o tamanho de fonte escolhido (px).
    """
    text = normalize_session_title_line(text)
    label.setWordWrap(False)
    label.setText(text)

    if not text:
        return max_font_px

    widget_w = effective_label_content_width(label, max_width_px)
    target_w = safe_content_width(
        max(widget_w, int(max_width_px)),
        extra_pad_x,
        edge_margin_px=edge_margin_px if fill_width else edge_margin_px + 16,
    )

    font_high = _estimate_font_high_bound(text, target_w, int(max_font_px))
    best_size = _largest_font_that_fits(text, target_w, font_high)

    label.setAlignment(align)
    label.setFont(_session_title_font(best_size))

    # Confirma no widget real (evita cortar a última letra).
    limit = target_w - _CLIP_GUARD_PX
    while best_size > 12:
        fm = label.fontMetrics()
        if _text_render_width(fm, text) <= limit:
            break
        best_size -= 1
        label.setFont(_session_title_font(best_size))

    base_css = (
        "background: transparent; border: none; color: #ffffff; "
        "padding: 0; margin: 0;"
    )
    label.setStyleSheet(
        f"QLabel {{ {base_css} {extra_css} }}" if extra_css else f"QLabel {{ {base_css} }}"
    )
    return best_size


def ordered_screens(app: Optional[QApplication] = None) -> List[QScreen]:
    """Lista monitores em ordem estável (esquerda → direita, depois Y)."""
    app = app or QApplication.instance()
    if not app:
        return []
    screens = list(app.screens())
    screens.sort(key=lambda s: (s.geometry().x(), s.geometry().y()))
    return screens


def screen_choice_label(screen: QScreen, index: int, primary: Optional[QScreen]) -> str:
    """Rótulo amigável para combo de seleção de monitor."""
    name = screen.name() or f"Display {index + 1}"
    geo = screen.geometry()
    suffix = " — principal" if primary and screen == primary else ""
    return f"Monitor {index + 1}: {name} ({geo.width()}×{geo.height()}){suffix}"


def list_screen_choices(app: Optional[QApplication] = None) -> List[Tuple[int, str]]:
    """Retorna [(índice, rótulo), ...] para QComboBox."""
    app = app or QApplication.instance()
    screens = ordered_screens(app)
    if not app or not screens:
        return []
    primary = app.primaryScreen()
    return [(i, screen_choice_label(s, i, primary)) for i, s in enumerate(screens)]


def resolve_public_screen(
    screen_index: Optional[int] = None,
    session_config=None,
    app: Optional[QApplication] = None,
) -> Optional[QScreen]:
    """
    Resolve o QScreen da tela do público.
    Por padrão usa índice 1 (segundo monitor). Com 1 monitor, usa o único disponível.
    """
    app = app or QApplication.instance()
    screens = ordered_screens(app)
    if not screens:
        return None

    if screen_index is None and session_config is not None:
        screen_index = session_config.get_public_screen_index()
    if screen_index is None:
        screen_index = 1

    if len(screens) == 1:
        return screens[0]

    if screen_index < 0:
        screen_index = 0
    if screen_index >= len(screens):
        screen_index = len(screens) - 1

    return screens[screen_index]


def apply_public_screen_fullscreen(
    window: QWidget,
    session_config=None,
    window_name: str = "Tela do público",
) -> None:
    """Exibe a janela em fullscreen no monitor configurado."""
    app = QApplication.instance()
    target_screen = resolve_public_screen(session_config=session_config, app=app)

    if not target_screen:
        window.showFullScreen()
        return

    try:
        handle = window.windowHandle()
        if handle:
            handle.setScreen(target_screen)
    except Exception as e:
        print(f"⚠️ {window_name}: falha ao definir monitor ({e})")

    window.setGeometry(target_screen.geometry())

    if sys.platform == "darwin":
        window.showNormal()
        window.show()
        QTimer.singleShot(120, window.showFullScreen)
        QTimer.singleShot(
            320,
            lambda: _retry_macos_fullscreen(window, session_config, window_name, 1),
        )
    else:
        window.showFullScreen()

    screens = ordered_screens(app)
    idx = screens.index(target_screen) if target_screen in screens else -1
    monitor_num = idx + 1 if idx >= 0 else "?"
    print(f"✅ {window_name} → Monitor {monitor_num}: {target_screen.name()}")


def _retry_macos_fullscreen(
    window: QWidget,
    session_config,
    window_name: str,
    attempt: int,
) -> None:
    if sys.platform != "darwin" or attempt > 4:
        return

    app = QApplication.instance()
    if not app:
        return

    target_screen = resolve_public_screen(session_config=session_config, app=app)
    if not target_screen:
        return

    if window.screen() == target_screen:
        return

    try:
        handle = window.windowHandle()
        if handle:
            handle.setScreen(target_screen)
    except Exception:
        pass

    window.showNormal()
    window.setGeometry(target_screen.geometry())
    window.showFullScreen()
    QTimer.singleShot(
        180,
        lambda: _retry_macos_fullscreen(window, session_config, window_name, attempt + 1),
    )
