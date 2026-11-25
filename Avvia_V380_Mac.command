#!/bin/bash
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
printf '\nCamocchio 3.14.39 - lascia aperto il Terminale. Per terminare: Ferma Live, poi Esci.\n'
cd "$HERE/src"
exec /usr/bin/python3 "$HERE/src/app.py"
