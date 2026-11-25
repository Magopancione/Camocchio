"""Local synthetic media only; no camera, credentials or network."""
import sys,tempfile,subprocess,time,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import live_av as m

def ff(*args):subprocess.run(['ffmpeg','-v','error',*args],check=True,timeout=20)
def mode(cfg,inputs,expected):
 ctx=SimpleNamespace(cfg=lambda:cfg,pw=lambda:'test-only',ffmpeg=lambda:'ffmpeg');relay=m.LiveAV(ctx);builder=m.hls_command
 try:
  with patch.object(m,'hls_command',side_effect=lambda exe,_,folder,*mode:builder(exe,inputs,folder,*mode)):relay.start()
  end=time.monotonic()+16
  while not relay.status()['ready'] and relay.status()['running'] and time.monotonic()<end:time.sleep(.1)
  state=relay.status();assert state['ready'] and state['audio']==expected,state
  folder=relay.session['directory'];segment=next(folder.glob('*.ts'))
  info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(segment)],timeout=5))
  assert {s['codec_type'] for s in info['streams']}==({'audio','video'} if expected else {'video'})
  if expected:
   audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(segment),'-vn','-f','s16le','-'],timeout=5)
   assert len(audio)>1000 and len(set(audio))>10
 finally:
  saved=relay.session;relay.stop();relay.stop()
  assert not relay.status()['running']
  if saved:assert not saved['directory'].exists()
with tempfile.TemporaryDirectory() as td:
 video=str(Path(td)/'video.mp4');audio=str(Path(td)/'audio.wav')
 ff('-f','lavfi','-i','testsrc2=size=160x90:rate=20:duration=4','-c:v','libx264',video)
 ff('-f','lavfi','-i','sine=frequency=440:sample_rate=8000:duration=4',audio)
 cfg={'host':'fixture.invalid','rtsp_path':'/video'}
 mode(cfg,['-re','-i',video],False)
 mode(dict(cfg,rtsp_audio_path='/audio'),['-re','-i',video,'-i',audio],True)
 mode(cfg,['-re','-i',video],False)
 with patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'{"streams":[{"codec_type":"audio","codec_name":"pcm_alaw"}]}')):
  assert m.inspect_source('ffprobe',dict(cfg,rtsp_audio_path='/audio'),'')[1]['audio']==['pcm_alaw']
 with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('probe',9)):
  assert m.inspect_source('ffprobe',cfg,'')==[{'source':0,'ok':False}]
 print('PASS Live: video-only, separate real HLS audio payload, restart, cleanup, bounded probe responses')
