import shutil
FFMPEG=shutil.which("ffmpeg")
FFPROBE=shutil.which("ffprobe")
if not FFMPEG or not FFPROBE:raise RuntimeError("Installare FFmpeg e FFprobe per il test di integrazione")
import sys,tempfile,subprocess,json,importlib.util
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));import motion_preview as m
spec=importlib.util.spec_from_file_location('app19',root/'src/app.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
with tempfile.TemporaryDirectory() as td:
 td=Path(td);video=td/'synthetic.mp4';static=td/'static.mp4'
 # Explicit synthetic fixture, no real footage: moving rectangle in two separate time windows.
 frames=[]
 for i in range(120):
  b=bytearray([30]*(160*90));t=i/10
  if 1<=t<3 or 8<=t<10:
   x=10+(i*7)%105
   for y in range(25,65):b[y*160+x:y*160+x+30]=bytes([220])*30
  frames.append(bytes(b))
 for path,data in [(video,b''.join(frames)),(static,bytes([30])*(160*90*120))]:
  r=subprocess.run([FFMPEG,'-y','-v','error','-f','rawvideo','-pix_fmt','gray','-s','160x90','-r','10','-i','pipe:0','-c:v','libx264','-pix_fmt','yuv420p',str(path)],input=data,capture_output=True);assert r.returncode==0,r.stderr
 events,scores=m.analyze(video,0,12,'medium',FFMPEG);print('Events:',events);assert len(events)==2,events
 times=m.choose_times(events,12);assert len(times)==12 and sum(t<6 for t in times)==6
 conf={'preview_mode':'motion','preview_frames':12,'motion_frames':12,'motion_seconds':3,'preview_seconds':3,'preview_start':0,'preview_end':12,'motion_sensitivity':'medium'}
 def uniform(*args):
  with patch.object(app,'cfg',return_value=conf),patch.object(app,'ffmpeg',return_value=FFMPEG),patch.object(app,'log'):
   app.makegif_uniform(*args)
 report=m.generate(video,td/'motion.gif',12,conf,FFMPEG,uniform,print);assert report['fallback'] is None,report
 meta=json.loads(subprocess.check_output([FFPROBE,'-v','error','-count_frames','-show_entries','stream=nb_read_frames:format=duration','-of','json',str(td/'motion.gif')]))
 assert int(meta['streams'][0]['nb_read_frames'])==12,meta
 assert abs(float(meta['format']['duration'])-3)<.1,meta
 print('PASS: actual GIF has 12 frames and 3-second duration')
 report=m.generate(static,td/'fallback.gif',12,conf,FFMPEG,uniform,print);assert report['fallback']=='no_significant_motion' and (td/'fallback.gif').exists()
 print('PASS: static video falls back to original uniform generator')
