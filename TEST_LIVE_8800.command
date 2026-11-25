#!/bin/bash
set -eu
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
echo 'Chiudi Camocchio e il Live ufficiale. Prova solo sulla tua telecamera configurata.'
echo 'Quando inizia il test, fai un breve suono vicino alla telecamera.'
printf 'Premi Invio per continuare, oppure Ctrl+C per annullare: '
read -r answer
exec /usr/bin/python3 scripts/live_8800.py
