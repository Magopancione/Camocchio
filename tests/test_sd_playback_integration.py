import sys,subprocess,tempfile,threading,struct,io,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));import sd_playback as sd
import app
# Synthetic HEVC fixture; fake protocol transport, real FFmpeg pipeline.
with tempfile.TemporaryDirectory() as td:
 td=Path(td);raw=td/'test.hevc'
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=20:duration=2','-c:v','libx265','-x265-params','log-level=error','-f','hevc',str(raw)],check=True,stderr=subprocess.DEVNULL)
 body=raw.read_bytes();fh=bytearray(22);struct.pack_into('<H',fh,4,40);struct.pack_into('<I',fh,18,len(body));payload=bytes(fh)+body
 ack=bytearray(64);struct.pack_into('<I',ack,0,463);struct.pack_into('<i',ack,4,1000)
 packet=struct.pack('<BBHHH',0x7f,0,1,len(payload),0)+payload+bytes([0xef])+bytes(7)
 class Sock:
  def __init__(self):self.b=io.BytesIO(bytes(ack)+packet);self.closed=False
  def recv(self,n):return self.b.read(n)
  def sendall(self,x):pass
  def settimeout(self,x):pass
  def shutdown(self,x):pass
  def close(self):self.closed=True
 class Handler:
  def __init__(self):self.wfile=io.BytesIO();self.codes=[]
  def send_response(self,c):self.codes.append(c)
  def send_header(self,*a):pass
  def end_headers(self):pass
  def send_error(self,c):self.codes.append(c)
 context=SimpleNamespace(JOB_LOCK=threading.Lock(),STATE={'segments':[dict(id=1,type=3,start=1,end=3)]},runtime=lambda:{'host':'fixture','port':8800,'device_id':0},ffmpeg=lambda:'ffmpeg',login=lambda c:(1,1),key=lambda t:b'',clock=lambda *a:None,exact=app.exact,sendpb=lambda *a:None,VIDEO={40},payload=lambda b,k:b)
 pb=sd.Playback(context)
 with patch.object(sd.Path,'exists',return_value=True),patch.object(sd.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
  pb.start(0,12345,target='VLC')
 try:
  pb.start(0,12345,target='VLC');raise AssertionError('concurrent start allowed')
 except RuntimeError:pass
 h=Handler();sock=Sock()
 with patch.object(sd.socket,'create_connection',return_value=sock):pb.serve(h,pb.session['token'])
 assert h.codes==[200],h.codes
 ts=td/'test.ts';ts.write_bytes(h.wfile.getvalue());assert ts.stat().st_size>0,pb.status()
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name','-of','json',str(ts)]));assert info['streams'][0]['codec_name']=='h264',info
 assert not context.JOB_LOCK.locked() and sock.closed and not pb.status()['running']
 print('PASS: synthetic HEVC -> fake camera framing -> real FFmpeg -> HTTP MPEG-TS H264; socket/process/lock cleanup')
 with patch.object(sd.Path,'exists',return_value=True),patch.object(sd.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
  pb.start(0,12345,target='VLC');pb.stop();pb.stop();assert not context.JOB_LOCK.locked()
 print('PASS: concurrent sessions blocked; stop before player connection idempotent')
