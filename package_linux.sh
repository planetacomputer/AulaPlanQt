#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ENV="$APP_DIR/.venv-build"

python3 -m venv "$BUILD_ENV"
"$BUILD_ENV/bin/python" -m pip install --upgrade pip
"$BUILD_ENV/bin/python" -m pip install PyInstaller PyQt6

mkdir -p "$APP_DIR/build"
QT_QPA_PLATFORM=offscreen "$BUILD_ENV/bin/python" - "$APP_DIR/build/aulaplan.png" <<'PY'
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

app = QApplication([])
pixmap = QPixmap(256, 256)
pixmap.fill(Qt.GlobalColor.transparent)
font = QFont()
font.setPixelSize(208)
painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
painter.setFont(font)
painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🏫")
painter.end()
if not pixmap.save(sys.argv[1], "PNG"):
    raise RuntimeError(f"Could not save application icon to {sys.argv[1]}")
PY

"$BUILD_ENV/bin/pyinstaller" \
    --clean \
    --noconfirm \
    --onefile \
    --windowed \
    --name AulaPlan \
    --icon "$APP_DIR/build/aulaplan.png" \
    --add-data "$APP_DIR/config_default.json:." \
    --distpath "$APP_DIR/dist" \
    --workpath "$APP_DIR/build" \
    --specpath "$APP_DIR/build" \
    "$APP_DIR/main.py"

printf 'Built standalone Linux application: %s/dist/AulaPlan\n' "$APP_DIR"
