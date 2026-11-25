from pathlib import Path
import json,socket,struct,subprocess,sys,threading
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import live_8800 as probe

def media(fmt,source,options):
    return subprocess.check_output(['ffmpeg','-v','error','-f','lavfi','-i',source,*options,'-f',fmt,'pipe:1'],timeout=10)

def packet(kind,data):
    parts=[data[i:i+500] for i in range(0,len(data),500)]
    for i,part in enumerate(parts):
        h=bytearray(12);h[:2]=bytes([127,kind]);struct.pack_into('<HHH',h,3,len(parts),i,len(part));yield bytes(h)+part

video=media('h264','testsrc2=size=96x64:rate=10:duration=1',['-c:v','libx264','-preset','ultrafast'])
audio=media('adts','sine=frequency=440:sample_rate=8000:duration=1',['-c:a','aac'])
data=b'\x1f'+bytes(11)+b''.join(packet(0,video))+b''.join(packet(0x1a,audio))
for quality,response in [(0,1001),(1,402),(0,-999)]:
    with socket.socket() as srv:
        srv.bind(('127.0.0.1',0));srv.listen();srv.settimeout(4);address=srv.getsockname();dial=socket.create_connection;seen=[]
        def exchange():
            with srv.accept()[0] as conn:
                conn.settimeout(3);req=probe.app.exact(conn,256);seen.append(req)
                reply=struct.pack('<IiHII',401,response,20,96,64).ljust(412,b'\0');conn.sendall(reply[:9]);conn.sendall(reply[9:]);
                if response in (1001,402):
                    seen.append(probe.app.exact(conn,412));conn.sendall(data)
        t=threading.Thread(target=exchange);t.start()
        with patch.object(probe.app,'login',return_value=(98765,31)) as login,patch.object(probe.socket,'create_connection',side_effect=lambda addr,timeout:dial(address,timeout)) as net:
            r=probe.attempt({'host':'192.168.1.5','port':8800,'device_id':123,'password':'hidden'},quality,4,'ffmpeg');assert net.call_args.args[0]==('192.168.1.5',8800);assert login.call_count==1
        t.join(4);assert not t.is_alive();assert struct.unpack_from('<I',seen[0])[0]==301 and struct.unpack_from('<I',seen[0],26)[0]==quality
        if response in (1001,402):
            assert struct.unpack_from('<Ii',seen[1])==(303,response);assert r['video']['codec']=='h264' and r['video']['frame_decodificati']>0,r
            assert r['audio']['aac_campioni_decodificati']>0 and r['audio']['aac_picco_pcm']>0,r
        else:assert len(seen)==1 and not r['richiesta_live_inviata']
        assert all(x not in json.dumps(r) for x in ('hidden','98765','192.168.1.5'))
assert probe.audio_candidate(bytes(256))[0]=='ima_compatibile'
assert probe.audio_candidate(b'\xff\xf1'+bytes(5))[0]==''
with patch.object(probe.app,'login',side_effect=RuntimeError('hidden')),patch.object(probe.socket,'create_connection') as net:
    assert not probe.attempt({},0,1,None)['login'];net.assert_not_called()
print('PASS active LAN fixture: authenticated setup, both profiles, real video/AAC decoding, refusal and no leaked secrets')
# Exercise the alternate codec and ticket-derived candidate decryption in memory.
hevc=media('hevc','testsrc2=size=96x64:rate=8:duration=1',['-c:v','libx265','-x265-params','pools=1:frame-threads=1:log-level=error'])
k=probe.app.key(98765);data=bytearray(bytes(16)+hevc);offsets=list(range(0,len(data)-63,80))
enc=probe.app.aes(k,b''.join(data[p:p+64] for p in offsets))
for i,p in enumerate(offsets):data[p:p+64]=enc[i*64:i*64+64]
assert probe.analyze([(0x28,bytes(data))],98765,'ffmpeg')['video']['codec']=='hevc'
print('PASS diagnostic: encrypted HEVC candidate, decoded frames without retaining media')
