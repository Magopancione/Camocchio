#!/usr/bin/env python3
"""Bounded, authenticated LAN viewing diagnostic. Output is aggregate JSON only."""
import argparse
from collections import Counter
import ipaddress
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app
from sd_playback import decode_ima_block

# LAN preview request and 12-byte media envelope documented by prsyahmi/v380.
# See docs/DIAGNOSTICA_8800.md. This is not the microSD playback command.
PRIVATE=[ipaddress.ip_network(s) for s in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','169.254.0.0/16')]
VIDEO_TYPES={0,1,0x28,0x29,0x32,0x33,0x34,0x35}
AUDIO_TYPES={0x16,0x1a}
LIMIT=8*1024*1024


def exact_until(sock,size,end):
    chunks=bytearray()
    while len(chunks)<size:
        left=end-time.monotonic()
        if left<=0:raise socket.timeout()
        sock.settimeout(min(3,left))
        data=sock.recv(size-len(chunks))
        if not data:raise EOFError()
        chunks.extend(data)
    return bytes(chunks)


def setup(sock,camera_id,ticket,quality):
    request=bytearray(256)
    struct.pack_into('<II',request,0,301,camera_id)
    struct.pack_into('<H',request,12,20)
    struct.pack_into('<I',request,14,ticket)
    struct.pack_into('<II',request,22,4097,quality)
    sock.sendall(request)
    end=time.monotonic()+5
    reply=bytearray(exact_until(sock,18,end))
    # Public client allows up to 412 bytes. Allow briefly for remaining TCP fragments.
    quiet=time.monotonic()+.25
    while len(reply)<412 and time.monotonic()<quiet:
        sock.settimeout(max(.001,quiet-time.monotonic()))
        try:data=sock.recv(412-len(reply))
        except socket.timeout:break
        if not data:break
        reply.extend(data)
    command,code=struct.unpack_from('<Ii',reply)
    accepted=command==401 and code in (402,1001,-11,-12)
    if accepted:
        start=bytearray(reply.ljust(412,b'\0'))
        struct.pack_into('<Ii',start,0,303,code)
        sock.settimeout(3);sock.sendall(start)
    return {'comando':command,'stato':code,'accettata':accepted,'byte_risposta':len(reply)}


def receive(sock,seconds):
    end=time.monotonic()+seconds;frames=[];types=Counter();controls=Counter();pending={};total_bytes=0;packet_count=0;drops=0
    reason='finestra_completata'
    try:
        while total_bytes<LIMIT and packet_count<24000:
            h=exact_until(sock,12,end);total_bytes+=12;packet_count+=1
            if h[0]!=0x7f:
                if packet_count==1 or h[0] in (0x1f,0x6f):controls[f'{h[0]:02x}']+=1;continue
                reason='intestazione_non_riconosciuta';break
            count,index,size=struct.unpack_from('<HHH',h,3)
            if not 0<=index<count<=8192 or not 1<=size<=8192:
                reason='frammento_non_compatibile';break
            if total_bytes+size>LIMIT:reason='limite_byte';break
            body=exact_until(sock,size,end);total_bytes+=size;kind=h[1];types[f'{kind:02x}']+=1
            if kind not in VIDEO_TYPES|AUDIO_TYPES:continue
            if index==0:pending[kind]=(count,0,bytearray())
            state=pending.get(kind)
            if not state or state[:2]!=(count,index) or len(state[2])+size>2*1024*1024:
                pending.pop(kind,None);drops+=1;continue
            state[2].extend(body)
            if index+1==count:
                frames.append((kind,bytes(state[2])));pending.pop(kind)
            else:pending[kind]=(count,index+1,state[2])
        else:reason='limite_diagnostica'
    except socket.timeout:reason='finestra_completata' if time.monotonic()>=end-.05 else 'timeout_senza_dati'
    except (EOFError,OSError):reason='connessione_chiusa'
    return frames,dict(byte_ricevuti=total_bytes,pacchetti_per_tipo=dict(types),controlli=dict(controls),frammenti_scartati=drops,frame_ricomposti=len(frames),fine=reason)


def annexb(data):
    m=re.search(rb'\x00\x00(?:\x00)?\x01',data[:36])
    return data[m.start():] if m and m.end()<len(data) else b''


def audio_candidate(data):
    # Recognize bounded, complete ADTS frames, not merely a sync marker.
    for off in (0,16,20):
        body=data[off:];i=0
        while i+7<=len(body) and body[i]==255 and body[i+1]&0xf6==0xf0:
            n=((body[i+3]&3)<<11)|(body[i+4]<<3)|(body[i+5]>>5)
            if n<7 or i+n>len(body):break
            i+=n
        if i and i==len(body):return 'aac',body
    for off in (0,20):
        body=data[off:]
        if body and len(body)%256==0 and all(body[i+2]<=88 and body[i+3]==0 for i in range(0,len(body),256)):
            return 'ima_compatibile',body
    return '',b''


def decoded(ffmpeg,fmt,data,kind):
    args=[ffmpeg,'-nostdin','-v','error','-threads','2','-f',fmt,'-i','pipe:0']
    if kind=='video':args+=['-an','-vf','scale=64:36','-frames:v','12','-f','framehash','pipe:1']
    else:args+=['-vn','-t','4','-ac','1','-ar','8000','-f','s16le','pipe:1']
    try:result=subprocess.run(args,input=data,capture_output=True,timeout=8)
    except (OSError,subprocess.TimeoutExpired):return 0,0
    if kind=='video':return sum(1 for line in result.stdout.splitlines() if re.match(rb'^\s*0,',line)),0
    samples=list(struct.iter_unpack('<h',result.stdout[:len(result.stdout)//2*2]));return len(samples),max((abs(x[0]) for x in samples),default=0)


def analyze(frames,ticket,ffmpeg):
    video=bytearray();audio=Counter();ima=bytearray();aac=bytearray();v_count=a_count=0;key=app.key(ticket)
    for kind,data in frames:
        if kind in VIDEO_TYPES and v_count<100 and len(video)<2*1024*1024:
            v_count+=1;part=annexb(data)
            if not part:part=annexb(app.decvid(data,key))
            video.extend(part[:max(0,2*1024*1024-len(video))])
        elif kind in AUDIO_TYPES and a_count<120:
            a_count+=1;form,body=audio_candidate(data)
            if not form and len(data)>=16:
                cut=len(data)//16*16
                # Test only codec signatures after the candidate transformation.
                form,body=audio_candidate(app.aes(key,data[:cut],True)+data[cut:])
            if form=='aac':aac.extend(body);audio['aac_frame_contenitore']+=1
            elif form=='ima_compatibile':
                for i in range(0,len(body),256):
                    if len(ima)>=64000:break
                    ima.extend(decode_ima_block(body[i:i+256]));audio['blocchi_compatibili_ima']+=1
    result={'video':{'frame_decodificati':0},'audio':{'frame_candidati_analizzati':a_count,**audio}}
    if video and ffmpeg:
        for fmt in ('h264','hevc'):
            count,_=decoded(ffmpeg,fmt,bytes(video),'video')
            if count:result['video']={'codec':fmt,'frame_decodificati':count};break
    if aac and ffmpeg:
        count,peak=decoded(ffmpeg,'aac',bytes(aac),'audio');result['audio'].update(aac_campioni_decodificati=count,aac_picco_pcm=peak)
    if ima:
        result['audio'].update(ima_campioni_compatibili=len(ima)//2,ima_picco_indicativo=max(abs(x[0]) for x in struct.iter_unpack('<h',ima)))
    return result


def attempt(c,quality,seconds,ffmpeg):
    r={'profilo':('alta' if quality else 'bassa'),'login':False,'richiesta_live_inviata':False}
    try:ticket,version=app.login(c)
    except (RuntimeError,ValueError,OSError):return dict(r,esito='login_non_confermato')
    r.update(login=True,versione_protocollo=version)
    if not ticket:return dict(r,esito='login_senza_ticket_utilizzabile')
    try:
        with socket.create_connection((c['host'],8800),timeout=4) as sock:
            r['setup']=setup(sock,c['device_id'],ticket,quality)
            if not r['setup']['accettata']:return dict(r,esito='risposta_setup_non_compatibile')
            r['richiesta_live_inviata']=True
            frames,counts=receive(sock,seconds)
        r.update(counts);r.update(analyze(frames,ticket,ffmpeg))
    except (RuntimeError,OSError,ValueError,EOFError):return dict(r,esito='lettura_o_analisi_interrotta')
    r['esito']='video_live_decodificato' if r['video']['frame_decodificati'] else 'video_live_non_confermato'
    return r


def main():
    parser=argparse.ArgumentParser(description='Diagnostica LAN, solo telecamera Camocchio salvata e TCP 8800')
    parser.add_argument('--deep',action='store_true',help='Prova profili bassa e alta, fino a 12 secondi ciascuno')
    args=parser.parse_args()
    try:
        cfg=app.cfg();addr=ipaddress.IPv4Address(cfg.get('host',''))
        if cfg['port']!=8800 or not any(addr in network for network in PRIVATE):raise ValueError()
    except (ValueError,KeyError,TypeError):
        print('Serve una telecamera con IPv4 privata salvata e porta 8800. Nessuna prova inviata.');return 2
    try:
        result=subprocess.run(['/usr/bin/security','find-generic-password','-s',app.SERVICE,'-w'],capture_output=True,text=True,timeout=30)
        password=result.stdout.rstrip('\n') if result.returncode==0 else ''
    except (OSError,subprocess.TimeoutExpired):password=''
    user=str(cfg.get('username',''))
    if not password or len(password.encode())>31 or not 1<=len(user.encode())<=32 or not 1<=cfg['device_id']<=0xffffffff:
        print('Controlla credenziali e Device ID nelle impostazioni salvate. Nessuna prova inviata.');return 2
    try:ffmpeg=app.tool_path('ffmpeg')
    except RuntimeError:ffmpeg=None
    c=dict(host=str(addr),port=8800,username=user,device_id=cfg['device_id'],password=password)
    reports=[]
    for profile in ([0,1] if args.deep else [0]):
        reports.append(attempt(c,profile,12 if args.deep else 6,ffmpeg))
        if not reports[-1]['login']:break
    print(json.dumps({'porta':8800,'ffmpeg_disponibile':bool(ffmpeg),'prove':reports,'nota':'Un esito negativo non esclude altri profili o firmware. IMA compatibile e picco non provano audio udibile.'},indent=2,ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:sys.exit(130)
