#!/usr/bin/env python3
"""Gera fotos/icon.ico a partir de fotos/favicon.svg (para PyInstaller e Inno Setup)."""

from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_PATH = ROOT / "fotos" / "favicon.svg"
ICO_PATH = ROOT / "fotos" / "icon.ico"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _ensure_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"], check=True)


def _pixmap_to_pil(pixmap) -> "Image.Image":
    from PIL import Image
    from PySide6.QtCore import QBuffer, QIODevice

    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.toImage().save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


def gerar_icon_ico(svg_path: Path = SVG_PATH, ico_path: Path = ICO_PATH) -> Path:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    if not svg_path.is_file():
        raise FileNotFoundError(f"Logo nao encontrada: {svg_path}")

    _ensure_pillow()
    from PIL import Image

    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    icon = QIcon(str(svg_path))
    frames: list[Image.Image] = []
    for size in ICO_SIZES:
        pm = icon.pixmap(size, size)
        if pm.isNull():
            raise RuntimeError(f"Falha ao renderizar SVG em {size}px")
        frames.append(_pixmap_to_pil(pm))

    ico_path.parent.mkdir(parents=True, exist_ok=True)
    # Maior frame como base; Pillow embute as resoluções em sizes.
    frames[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
    )
    print(f"OK: {ico_path} ({ico_path.stat().st_size} bytes)")
    return ico_path


if __name__ == "__main__":
    gerar_icon_ico()
