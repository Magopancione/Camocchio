import sys,subprocess,tempfile,struct,io,json,threading,random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));import sd_playback as sd;import app
with tempfile.TemporaryDirectory() as td:
 td=Path(td)
 subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=8000:duration=2','-c:a','adpcm_ima_wav','-block_size','256',str(td/'ima.wav')],check=True)
 wav=(td/'ima.wav').read_bytes();off=12
 while wav[off:off+4]!=b'data':off+=8+struct.unpack_from('<I',wav,off+4)[0]+(struct.unpack_from('<I',wav,off+4)[0]%2)
 size=struct.unpack_from('<I',wav,off+4)[0];data=wav[off+8:off+8+size]
 reference=subprocess.check_output(['ffmpeg','-v','error','-i',str(td/'ima.wav'),'-f','s16le','pipe:1'])
 ours=b''.join(sd.decode_ima_block(data[i:i+256]) for i in range(0,len(data),256))
 # WAV fact can trim last block. Compare all shared samples.
 a=struct.unpack('<%dh'%(len(reference)//2),reference);b=struct.unpack('<%dh'%(len(ours)//2),ours)
 maxerr=max(abs(x-y) for x,y in zip(a,b));print('Decoder max absolute error vs FFmpeg:',maxerr);assert maxerr<=1
 raw=td/'test.hevc';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=20:duration=2','-c:v','libx265','-x265-params','log-level=error','-f','hevc',str(raw)],check=True,stderr=subprocess.DEVNULL)
 def frame(ft,body):
  h=bytearray(22);struct.pack_into('<H',h,4,ft);struct.pack_into('<I',h,18,len(body));return bytes(h)+body
 payload=frame(40,raw.read_bytes())+b''.join(frame(22,data[i:i+256]) for i in range(0,len(data),256))
 ack=bytearray(64);struct.pack_into('<I',ack,0,463);struct.pack_into('<i',ack,4,1000)
 packet=b''.join(struct.pack('<BBHHH',0x7f,0,i//30000,len(payload[i:i+30000]),0)+payload[i:i+30000] for i in range(0,len(payload),30000))+bytes([0xef])+bytes(7)
 class Sock:
  def __init__(self):self.b=io.BytesIO(bytes(ack)+packet)
  def recv(self,n):return self.b.read(n)
  def sendall(self,x):pass
  def settimeout(self,x):pass
  def shutdown(self,x):pass
  def close(self):pass
 class Handler:
  def __init__(self):self.wfile=io.BytesIO();self.codes=[]
  def send_response(self,c):self.codes.append(c)
  def send_header(self,*a):pass
  def end_headers(self):pass
  def send_error(self,*a):self.codes.append(a[0])
 ctx=SimpleNamespace(JOB_LOCK=threading.Lock(),STATE={'segments':[dict(id=1,type=3,start=1,end=3)]},runtime=lambda:{'host':'fixture','port':8800,'device_id':0},cfg=lambda:{'sd_stream_audio':True},ffmpeg=lambda:'ffmpeg',login=lambda c:(1,1),key=lambda t:b'',clock=lambda *a:None,exact=app.exact,sendpb=lambda *a:None,VIDEO={40},payload=lambda b,k:b)
 pb=sd.Playback(ctx)
 with patch.object(sd.Path,'exists',return_value=True),patch.object(sd.subprocess,'run',return_value=SimpleNamespace(returncode=0)):pb.start(0,12345,target='VLC')
 h=Handler()
 with patch.object(sd.socket,'create_connection',return_value=Sock()):pb.serve(h,pb.session['token'])
 assert h.codes==[200],(h.codes,pb.status());out=td/'stream.ts';out.write_bytes(h.wfile.getvalue())
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,sample_rate,channels','-of','json',str(out)]));codecs=[s['codec_name'] for s in info['streams']];assert 'h264' in codecs and 'aac' in codecs,info
 assert pb.status()['audio_requested'] and pb.status()['audio_blocks']>0 and pb.status()['audio_samples']>0 and pb.status()['audio_peak']>0
 assert not ctx.JOB_LOCK.locked();print('PASS: synthetic camera framing -> H264+AAC progressive HTTP; cleanup',info['streams'])

 # The same synthetic camera supplies an internal HLS playlist without launching an app.
 import time
 with patch.object(sd.socket,'create_connection',return_value=Sock()),patch.object(sd.subprocess,'run') as launch:
  assert pb.start(0,12345,target='internal')=={'target':'internal'}
  directory=pb.session['directory']
  limit=time.monotonic()+15
  while pb.status()['running'] and time.monotonic()<limit:time.sleep(.05)
  assert not launch.called
  status=pb.status();assert status.get('playlist'),status
  playlist=directory/'index.m3u8';assert '#EXT-X-ENDLIST' in playlist.read_text()
  h=Handler();pb.serve_hls(h,status['playlist']);assert h.codes==[200] and b'#EXTM3U' in h.wfile.getvalue()
  h=Handler();pb.serve_hls(h,'/sd-hls/invalid/index.m3u8');assert h.codes==[404]
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name','-of','json',str(playlist)]))
 assert {x['codec_name'] for x in meta['streams']}=={'h264','aac'},meta
 pb.stop();assert not directory.exists() and not ctx.JOB_LOCK.locked()
 print('PASS internal HLS with audio, no external launch, token check and cache cleanup')
