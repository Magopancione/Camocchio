#!/bin/bash
set -euo pipefail
trap 'rc=$?; echo "Build interrotta: $rc"; read -r -p "Premi Invio per chiudere..." _; exit "$rc"' ERR
cd "$(dirname "$0")"
if [ "$(uname -s)" != Darwin ]; then echo 'Compilazione disponibile solo su macOS'; exit 1; fi
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
PYTHON="${PYTHON_BUILD:-/usr/bin/python3}"
if [ ! -x "$PYTHON" ]; then PYTHON="$(command -v python3)"; fi
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,9), "Serve Python 3.9+ per compilare"'
command -v ffmpeg >/dev/null || { echo 'FFmpeg non trovato sul Mac di compilazione'; exit 1; }
command -v ffprobe >/dev/null || { echo 'FFprobe non trovato sul Mac di compilazione'; exit 1; }
"$PYTHON" -m venv .venv-build
.venv-build/bin/python -m pip install --upgrade pip
.venv-build/bin/python -m pip install -r requirements-build.txt
.venv-build/bin/python -m pip check
mkdir -p build-notices
ffmpeg -L > build-notices/FFmpeg-license.txt 2>&1
ffmpeg -buildconf > build-notices/FFmpeg-buildconf.txt 2>&1
.venv-build/bin/python -m pip freeze > build-notices/Python-packages.txt
.venv-build/bin/python -m PyInstaller --clean --noconfirm --distpath dist-native --workpath build-native macos/V380.spec
APP="$PWD/dist-native/Camocchio.app"
.venv-build/bin/python scripts/verify_native.py "$APP"
# Verify native bundle structure and collected dependencies; never disable Gatekeeper.
/usr/bin/codesign --verify --deep --strict "$APP"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP" "$PWD/Camocchio_Mac_3.14.42_NATIVE.zip"
echo "App creata: $APP"
echo 'Sposta Camocchio.app in Applicazioni e aprila dal Finder. Il Terminale serve solo per questa compilazione.'
open -R "$APP"
