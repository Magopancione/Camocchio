"""Post-build checks executed on the Mac that creates the .app."""
import os,subprocess,sys
from pathlib import Path
bundle=Path(sys.argv[1]).resolve()
exe=bundle/'Contents/MacOS/Camocchio'
if not exe.is_file():raise SystemExit('Eseguibile nativo assente')
info=subprocess.check_output(['/usr/bin/file',str(exe)],text=True)
if 'Mach-O' not in info:raise SystemExit('Il launcher non e un eseguibile Mach-O')
env=dict(os.environ,PATH='/usr/bin:/bin:/usr/sbin:/sbin')
for key in list(env):
 if key.startswith(('PYTHON','DYLD_')):env.pop(key,None)
for name in ('ffmpeg','ffprobe'):
 candidates=[p for p in bundle.rglob(name) if p.is_file() and p.parent.name=='bin']
 if not candidates:raise SystemExit(name+' non incluso')
 tool=candidates[0]
 subprocess.run([str(tool),'-version'],check=True,env=env,stdout=subprocess.DEVNULL,timeout=20)
 if name=='ffmpeg':
  enc=subprocess.check_output([str(tool),'-hide_banner','-encoders'],env=env,text=True,stderr=subprocess.DEVNULL)
  if 'libx264' not in enc or ' aac ' not in enc:raise SystemExit('FFmpeg richiede encoder libx264 e AAC')
print('PASS: eseguibile Mach-O, FFmpeg/FFprobe inclusi ed eseguibili con PATH minimo; verificare ora la finestra e la rete sul Mac')
