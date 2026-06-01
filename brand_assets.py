"""
Marca do sistema (favicon.svg) e foto do desenvolvedor (77593994.png).
"""

from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath

if TYPE_CHECKING:
    from session_config import SessionConfig

BRAND_LOGO_REL = os.path.join("fotos", "favicon.svg")
DEVELOPER_PHOTO_REL = os.path.join("fotos", "77593994.png")
LEGACY_LOGO_REL = os.path.join("fotos", "logo.png")
LEGACY_DEV_PHOTO_REL = os.path.join("fotos", "carlos.jpeg")


def resolve_asset(session_config: "SessionConfig", relative_path: str) -> Optional[str]:
    """Caminho absoluto em AppData ou bundle, se o arquivo existir."""
    for getter in (session_config.get_data_path, session_config.get_bundle_path):
        path = getter(relative_path)
        if path and os.path.isfile(path):
            return path
    return None


def resolve_brand_logo_path(session_config: "SessionConfig") -> Optional[str]:
    return (
        resolve_asset(session_config, BRAND_LOGO_REL)
        or resolve_asset(session_config, LEGACY_LOGO_REL)
    )


def resolve_developer_photo_path(session_config: "SessionConfig") -> Optional[str]:
    return (
        resolve_asset(session_config, DEVELOPER_PHOTO_REL)
        or resolve_asset(session_config, LEGACY_DEV_PHOTO_REL)
    )


def brand_icon(session_config: "SessionConfig") -> QIcon:
    path = resolve_brand_logo_path(session_config)
    return QIcon(path) if path else QIcon()


def brand_pixmap(
    session_config: "SessionConfig",
    width: int,
    height: Optional[int] = None,
) -> QPixmap:
    h = height if height is not None else width
    path = resolve_brand_logo_path(session_config)
    if not path:
        return QPixmap()
    return QIcon(path).pixmap(width, h, QIcon.Mode.Normal, QIcon.State.Off)


def developer_pixmap(session_config: "SessionConfig") -> QPixmap:
    path = resolve_developer_photo_path(session_config)
    if not path:
        return QPixmap()
    return QPixmap(path)


def circular_pixmap(source: QPixmap, size: int) -> QPixmap:
    """Recorte circular para avatar (foto do desenvolvedor)."""
    if source.isNull():
        return QPixmap()
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    scaled = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return out
