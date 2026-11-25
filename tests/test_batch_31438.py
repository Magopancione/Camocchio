import sys,tempfile,subprocess,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'));import app
with tempfile.TemporaryDirectory() as tmp:
 base=Path(tmp);thumb=base/'Thumbnails';thumb.mkdir();v=base/'V380_2026-01-01_10-00-00.mp4';existing=base/'V380_2026-01-01_10-05-00.mp4';bad=base/'V380_2026-01-01_10-10-00.mp4';old=thumb/(existing.stem+'.gif');old.write_bytes(b'unchanged');existing.touch();bad.touch();(base/'other.mp4').touch();(base/'V380_2026-01-01_10-15-00.partial.mp4').touch()
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=96x64:rate=8:duration=2','-c:v','libx264',str(v)],check=True)
 with patch.object(app,'paths',return_value=(base,thumb)),patch.object(app,'cfg',return_value={'preview_mode':'uniform','preview_start':0,'preview_end':2,'preview_frames':6,'preview_seconds':2}),patch.object(app,'log'):
  app.start_preview_batch();end=time.monotonic()+20
  while app.BATCH['running'] and time.monotonic()<end:time.sleep(.05)
  assert not app.BATCH['running'] and '1 create' in app.BATCH['message'] and '1 errori' in app.BATCH['message'],app.BATCH
  assert (thumb/(v.stem+'.gif')).read_bytes().startswith(b'GIF') and old.read_bytes()==b'unchanged'
  assert len(list(thumb.glob('*.gif')))==2 and not list(thumb.glob('.camocchio-gif-*'))
 print('PASS batch: complete GIF, old GIF preserved, failing/foreign/partial files excluded from results')
