"""Synthetic camera on loopback; real FFmpeg, no user media or credentials."""
import io,json,re,socket,struct,subprocess,sys,threading,time,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app,live_av,native_live

class Handler:
    def __init__(self):self.code=None;self.wfile=io.BytesIO()
    def send_error(self,c):self.code=c
    def send_response(self,c):self.code=c
    def send_header(self,*args):pass
    def end_headers(self):pass

def packet(kind,body):
    chunks=[body[i:i+1000] for i in range(0,len(body),1000)]
    for i,chunk in enumerate(chunks):
        h=bytearray(12);h[:2]=bytes([127,kind]);struct.pack_into('<HHH',h,3,len(chunks),i,len(chunk));yield h+chunk

def wait(predicate,seconds):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if predicate():return True
        time.sleep(.025)
    return False

raw=subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=128x72:rate=20:duration=1','-c:v','libx265','-preset','ultrafast','-x265-params','pools=1:frame-threads=1:log-level=error:aud=1:bframes=0:keyint=20:repeat-headers=1','-f','hevc','pipe:1'],capture_output=True,check=True,timeout=12).stdout
starts=[m.start() for m in native_live.START.finditer(raw) if (raw[m.end()]>>1)&63==35]+[len(raw)]
pictures=[raw[a:b] for a,b in zip(starts,starts[1:])];assert len(pictures)==20
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'test.wav'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=8000:duration=1','-c:a','adpcm_ima_wav','-block_size','256',str(p)],check=True,timeout=10)
    data=p.read_bytes();off=data.index(b'data')+8;size=struct.unpack_from('<I',data,off-4)[0];blocks=[data[i:i+256] for i in range(off,off+size,256)]

ctx=SimpleNamespace(JOB_LOCK=threading.Lock(),cfg=lambda:{'host':'192.168.10.3','port':8800},runtime=lambda:dict(device_id=99,username='99',password='test-only'),ffmpeg=lambda:'ffmpeg',login=lambda c:(12,3),key=app.key,decvid=app.decvid)
live=live_av.LiveAV(ctx)
with ctx.JOB_LOCK:
    try:live.start_native();raise AssertionError('busy allowed')
    except RuntimeError as err:assert 'microSD' in str(err)

def exercise(case,quality="low"):
    with socket.socket() as server:
        server.bind(('127.0.0.1',0));server.listen();server.settimeout(4);addr=server.getsockname();dial=socket.create_connection
        done=threading.Event(); errors=[]
        def camera():
            try:
                with server.accept()[0] as s:
                    request=native_live.exact(s,256);assert struct.unpack_from('<I',request)[0]==301
                    assert struct.unpack_from('<I',request,14)[0]==12
                    assert struct.unpack_from('<I',request,26)[0]==int(quality=='high')
                    s.sendall(struct.pack('<Ii',401,1001 if case!='reject' else -999).ljust(32,b'\0'))
                    if case=='reject':return
                    start=native_live.exact(s,412);assert struct.unpack_from('<I',start)[0]==303
                    if case=='stall':
                        assert s.recv(1)==b'';return
                    now=time.monotonic();v=a=0
                    key=app.key(12)
                    while not done.is_set():
                        if v/20<=a*505/8000:
                            due=v/20;kind=0x28 if v%20==0 else 0x29;body=pictures[v%20];v+=1
                            if v%20==1:
                                body=bytearray(bytes(16)+body)
                                offsets=list(range(0,len(body)-63,80));encrypted=app.aes(key,b''.join(body[i:i+64] for i in offsets))
                                for j,i in enumerate(offsets):body[i:i+64]=encrypted[j*64:j*64+64]
                        else:
                            due=a*505/8000;kind=0x16;body=bytes(16)+blocks[a%len(blocks)];a+=1
                        done.wait(max(0,now+due-time.monotonic()))
                        if not done.is_set():
                            for fragment in packet(kind,body):s.sendall(fragment)
            except (BrokenPipeError,ConnectionResetError):pass
            except Exception as e:errors.append(str(e))
        worker=threading.Thread(target=camera,daemon=True);worker.start()
        try:
            with patch.object(native_live.socket,'create_connection',side_effect=lambda target,timeout:dial(addr,timeout)) as connect:
                live.start_native(quality);session=live.session;directory=session['directory']
                assert wait(lambda:connect.called,2)
                if case=='ok':
                    assert wait(lambda:live.status()['ready'] or live.status()['error'],14),live.status()
                    state=live.status();assert state['ready'] and state['audio'] and state['fps_estimated']==20,state
                    h=Handler();live.serve(h,state['url']);assert h.code==200 and b'#EXTM3U' in h.wfile.getvalue()
                    h=Handler();live.serve(h,'/live-av/wrong/live.m3u8');assert h.code==404
                    seg=sorted(directory.glob('*.ts'))[0]
                    codecs=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name','-of','json',str(seg)],timeout=6))
                    assert {s['codec_name'] for s in codecs['streams']}=={'h264','aac'}
                    assert state['quality']==quality
                    assert int(next(x.split(':')[1] for x in (directory/'live.m3u8').read_text().splitlines() if x.startswith('#EXT-X-TARGETDURATION:')))==2
                    pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(seg),'-vn','-f','s16le','pipe:1'],timeout=8)
                    assert len(pcm)>8000 and any(pcm)
                elif case=='reject':
                    assert wait(lambda:not live.status()['running'],5) and 'rifiutata' in live.status()['error'],live.status()
                    assert not directory.exists() and not ctx.JOB_LOCK.locked()
                else:
                    time.sleep(.4);assert live.status()['running'] and not live.status()['ready']
                assert connect.call_args.args[0]==('192.168.10.3',8800)
        finally:
            live.stop();live.stop();done.set();worker.join(3)
        assert not errors,errors
        assert not directory.exists() and not ctx.JOB_LOCK.locked()
        assert not live.status()['running'] and not worker.is_alive()

for scenario in ('ok','reject','stall'):exercise(scenario)
exercise('ok','high')
print('PASS: native 8800, encrypted HEVC, IMA -> audible-signal AAC, HLS token, refusal, stop during initialization, restart and cleanup')
