import sys,tempfile,subprocess,time,json,io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import live_av

with tempfile.TemporaryDirectory() as td:
    td=Path(td);fixture=td/'synthetic.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=20:duration=6',
                    '-f','lavfi','-i','sine=frequency=440:sample_rate=8000:duration=6','-c:v','libx264',
                    '-preset','ultrafast','-c:a','aac',str(fixture)],check=True)
    original=live_av.hls_command
    ctx=SimpleNamespace(cfg=lambda:{'host':'fixture.invalid','rtsp_auth':True,'username':'tester'},pw=lambda:'not-a-real-password',ffmpeg=lambda:'ffmpeg')
    relay=live_av.LiveAV(ctx)
    with patch.object(live_av,'hls_command',side_effect=lambda exe,args,d:original(exe,['-re','-stream_loop','-1','-i',str(fixture)],d)):
        relay.start()
    deadline=time.time()+20
    while not relay.status()['ready'] and time.time()<deadline:time.sleep(.2)
    state=relay.status();assert state['ready'] and state['audio'],state
    directory=relay.session['directory'];segment=next(directory.glob('*.ts'))
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name','-of','json',str(segment)]))
    codecs={s['codec_name'] for s in meta['streams']};assert {'h264','aac'}<=codecs,meta
    class Handler:
        def __init__(self):self.wfile=io.BytesIO();self.code=None
        def send_error(self,c):self.code=c
        def send_response(self,c):self.code=c
        def send_header(self,*args):pass
        def end_headers(self):pass
    handler=Handler();relay.serve(handler,state['url']);assert handler.code==200 and b'#EXTM3U' in handler.wfile.getvalue()
    handler=Handler();relay.serve(handler,'/live-av/wrong/live.m3u8');assert handler.code==404
    handler=Handler();relay.serve(handler,'/live-av/'+relay.session['token']+'/../config.json');assert handler.code==404
    assert 'password' not in json.dumps(state) and 'tester' not in json.dumps(state)
    relay.stop();relay.stop();assert not directory.exists() and not relay.status()['running']
    print('PASS Live AV: real FFmpeg synthetic audio/video -> HLS H264+AAC, HTTP token, traversal rejection, cleanup')
