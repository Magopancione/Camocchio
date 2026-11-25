import json,sys,subprocess,tempfile,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'));import live_av as m
with tempfile.TemporaryDirectory() as tmp:
 f=Path(tmp)/'test.flv';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=20:duration=4','-f','lavfi','-i','sine=frequency=500:duration=4','-c:v','libx264','-c:a','aac','-f','flv',str(f)],check=True);payload=f.read_bytes();redirect=False;paths=[]
 class Fixture(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   paths.append(self.path)
   if redirect:self.send_response(302);self.send_header('Location','/not-requested');self.end_headers();return
   self.send_response(200);self.end_headers();self.wfile.write(payload)
 server=ThreadingHTTPServer(('127.0.0.1',0),Fixture);threading.Thread(target=server.serve_forever,daemon=True).start();live=m.LiveAV(SimpleNamespace(cfg=lambda:{},ffmpeg=lambda:'ffmpeg'));url=f'http://127.0.0.1:{server.server_port}/live.flv'
 def wait(key):
  until=time.monotonic()+12
  while not live.status()[key] and time.monotonic()<until:time.sleep(.05)
 try:
  for i in range(2):
   live.start(relay=url);wait('ready');state=live.status();assert state['ready'] and state['audio'],state
   folder=live.session['directory'];segment=next(folder.glob('*.ts'));v=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name','-of','json',str(segment)]));assert {x['codec_name'] for x in v['streams']}=={'h264','aac'}
   live.stop();assert not folder.exists()
  redirect=True;live.start(relay=url);wait('error');assert 'Bridge locale' in live.status()['error'] and paths==['/live.flv']*3
  for u in ('http://localhost:12/live.flv','http://192.0.2.1:80/live.flv','file:///etc/passwd',url+'?x=1',''):
   try:m.local_relay_args(u);raise AssertionError('unsafe URL accepted')
   except ValueError:pass
 finally:live.stop();server.shutdown();server.server_close()
 print('PASS bridge: repeat FLV to H264/AAC HLS, stop cleanup, loopback only and no redirect')
