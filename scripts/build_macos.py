"""Build the real native application on macOS, including its Python runtime."""
from pathlib import Path
import subprocess,sys
if sys.platform!='darwin':raise SystemExit('La build nativa richiede macOS; nessuna .app generata su questo sistema')
root=Path(__file__).resolve().parents[1]
subprocess.run(['/bin/bash',str(root/'CREA_APP_MAC.command')],check=True,cwd=root)
