# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from contextlib import ExitStack
import socket,struct,subprocess,secrets,string,os,sys,json,shutil,threading,webbrowser,mimetypes
from datetime import datetime,timezone
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs,unquote
APP_KEY=b"macrovideo+*#!^@"; A=0x618123462C14795C; B=0x82800DF0; VIDEO={0,1,40,41,50,51,52,53}
CFG=Path.home()/"Library/Application Support/V380 Mac 2/config.json"; SERVICE="V380 Mac 2 Camera Password"; LOG=Path.home()/"Library/Logs/V380Mac2.log"
STATE={'segments':[],'busy':False,'progress':'','error':'','active_index':None,'progress_pct':0}
def log(x): LOG.parent.mkdir(parents=True,exist_ok=True);LOG.open('a').write(datetime.now().isoformat(timespec='seconds')+' '+str(x)+'\n')
def cfg():
 d={'host':'192.168.1.140','port':8800,'device_id':52405818,'username':'52405818','save_dir':'~/Movies/V380','camera_name':'Ingresso','time_correction':True,'library_page_size':12,'player':'VLC','language':'it','preview_frames':50,'preview_seconds':10.0,'preview_start':10.0,'preview_end':60.0}
 if CFG.exists():
  try:d.update(json.loads(CFG.read_text()))
  except Exception as e:log('CONFIG READ ERROR '+repr(e))
 # Normalize legacy/sparse configs so every UI field exists at startup.
 d['port']=int(d.get('port',8800));d['device_id']=int(d.get('device_id',52405818));d['library_page_size']='all' if str(d.get('library_page_size'))=='all' else int(d.get('library_page_size',12));d['preview_frames']=int(d.get('preview_frames',50));d['preview_seconds']=float(d.get('preview_seconds',10));d['preview_start']=float(d.get('preview_start',10));d['preview_end']=float(d.get('preview_end',60));d['time_correction']=bool(d.get('time_correction',True));d['language']=d.get('language','it') or 'it'
 return d
def pw():
 p=subprocess.run(['/usr/bin/security','find-generic-password','-s',SERVICE,'-w'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);return p.stdout.rstrip('\n') if p.returncode==0 else ''
def setpw(x):
 subprocess.run(['/usr/bin/security','delete-generic-password','-s',SERVICE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 p=subprocess.run(['/usr/bin/security','add-generic-password','-U','-s',SERVICE,'-a',os.environ.get('USER','user'),'-w',x],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr)
def runtime():
 d=cfg();p=pw()
 if not p:raise RuntimeError('Password non presente: apri Impostazioni')
 return {'host':d['host'],'port':int(d['port']),'device_id':int(d['device_id']),'username':d['username'],'password':p,'save_dir':Path(os.path.expanduser(d['save_dir']))}
def ffmpeg():
 for x in ['/opt/homebrew/bin/ffmpeg','/usr/local/bin/ffmpeg',shutil.which('ffmpeg')]:
  if x and Path(x).exists():return x
 raise RuntimeError('FFmpeg non trovato')
def pkcs7(x):n=16-len(x)%16;return x+bytes([n])*n
def aes(k,d,dec=False):
 a=['/usr/bin/openssl','enc','-aes-128-ecb']+(['-d'] if dec else [])+['-K',k.hex(),'-nosalt','-nopad'];p=subprocess.run(a,input=d,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 return p.stdout
def env(p):
 alpha=string.ascii_letters+string.digits;rk=''.join(secrets.choice(alpha) for _ in range(16)).encode();one=aes(APP_KEY,pkcs7(p.encode()));two=aes(rk,pkcs7(one));o=bytearray(64);o[:16]=rk;o[16:16+len(two)]=two;return bytes(o)
def exact(s,n):
 o=bytearray()
 while len(o)<n:
  x=s.recv(n-len(o))
  if not x:raise ConnectionError('Telecamera disconnessa')
  o+=x
 return bytes(o)
def clock(b,o,ts):
 t=datetime.fromtimestamp(ts,timezone.utc);struct.pack_into('<H',b,o,t.year);b[o+2:o+7]=bytes([t.month,t.day,t.hour,t.minute,t.second])
def login(c):
 q=bytearray(520);struct.pack_into('<I',q,0,1167);struct.pack_into('<I',q,4,120);q[8]=31;struct.pack_into('<I',q,9,10);struct.pack_into('<I',q,13,c['device_id']);st=datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode();q[17:17+len(st)]=st;u=c['username'].encode();q[49:49+len(u)]=u;q[81:145]=env(c['password'])
 with socket.create_connection((c['host'],c['port']),8) as s:s.settimeout(8);s.sendall(q);r=exact(s,256)
 cmd,res=struct.unpack_from('<I',r,0)[0],struct.unpack_from('<i',r,4)[0]
 if (cmd,res)!=(1168,1001):raise RuntimeError(f'Login fallito {cmd}/{res}')
 return struct.unpack_from('<I',r,13)[0],r[12]
def corrected_ts(ts,c):
 return ts-3600 if c.get('time_correction',True) else ts
def listrec(c,t,day):
 y,m,d=map(int,day.split('-'));q=bytearray(128)
 for o,v in [(0,361),(4,c['device_id']),(8,t),(58,1)]:struct.pack_into('<I',q,o,v)
 for o,v in [(14,y),(16,m),(18,d),(34,y),(36,m),(38,d),(40,23),(42,59),(44,59)]:struct.pack_into('<H',q,o,v)
 out=[]
 with socket.create_connection((c['host'],c['port']),8) as s:
  s.settimeout(8);s.sendall(q);a=exact(s,32)
  if struct.unpack_from('<I',a,0)[0]!=461:raise RuntimeError('Ricerca SD rifiutata')
  if struct.unpack_from('<i',a,4)[0]!=1:return []
  for _ in range(500):
   z=bytearray(32)
   for o,v in [(0,362),(4,c['device_id']),(8,t)]:struct.pack_into('<I',z,o,v)
   s.sendall(z);b=exact(s,512)
   if struct.unpack_from('<I',b,0)[0]!=462:break
   flag=struct.unpack_from('<H',b,4)[0];count=min(struct.unpack_from('<H',b,6)[0],38)
   for i in range(count):
    o=8+i*13;rid=struct.unpack_from('<I',b,o)[0];typ=b[o+4];st=struct.unpack_from('<I',b,o+5)[0];en=struct.unpack_from('<I',b,o+9)[0]
    if rid and en>st:out.append({'id':rid,'type':typ,'start':st,'end':en,'display_start':corrected_ts(st,c),'display_end':corrected_ts(en,c)})
   if flag==12:break
 return sorted(out,key=lambda x:x['start'])
def key(t):
 k=bytearray(16);struct.pack_into('<I',k,0,t);struct.pack_into('<Q',k,4,A);struct.pack_into('<I',k,12,B);return bytes(k)
def sc(d):
 w=d[:16];a=w.find(b'\0\0\0\1');b=w.find(b'\0\0\1');return a if a>=0 and (b<0 or a<=b) else b
def decvid(d,k):
 o=bytearray(d);offs=list(range(0,len(o)-63,80))
 if not offs:return bytes(o)
 x=aes(k,b''.join(bytes(o[i:i+64]) for i in offs),True)
 for n,i in enumerate(offs):o[i:i+64]=x[n*64:(n+1)*64]
 return bytes(o)
def payload(b,k):
 d=b if sc(b)>=0 else decvid(b,k);i=sc(d);return None if i<0 else d[i:]
def sendpb(s,g,mode,note=0,frame=0,pkt=0):
 a=bytearray(32);struct.pack_into('<I',a,0,364);a[4]=mode;a[5]=note;struct.pack_into('<H',a,6,200);struct.pack_into('<H',a,8,frame&0xffff);struct.pack_into('<I',a,12,g['id']);
 if mode==1:clock(a,16,g['start'])
 struct.pack_into('<H',a,23,pkt if mode==2 else 0);s.sendall(a)
def download(c,t,g,raw):
 k=key(t);q=bytearray(64)
 for o,v in [(0,363),(4,c['device_id']),(8,t),(12,g['id'])]:struct.pack_into('<I',q,o,v)
 clock(q,16,g['start']);q[23]=g['type'];pending=bytearray();lp=lf=ack=written=0;codec=None
 audio_path=Path(str(raw)+'.ima');audio_blocks=0;video_frames=0
 with ExitStack() as stack:
  s=stack.enter_context(socket.create_connection((c['host'],c['port']),20))
  f=stack.enter_context(open(raw,'wb'));af=stack.enter_context(audio_path.open('wb'))
  s.settimeout(20);s.sendall(q);r=exact(s,64)
  if struct.unpack_from('<I',r,0)[0]!=463 or struct.unpack_from('<i',r,4)[0]!=1000:raise RuntimeError('Playback rifiutato')
  sendpb(s,g,1)
  while True:
   h=exact(s,8);typ=h[0];note=h[1];pkt=struct.unpack_from('<H',h,2)[0];size=struct.unpack_from('<H',h,4)[0];pl=exact(s,size) if size else b''
   if typ==0xef:break
   if typ==0x1f:continue
   if typ==0x6f:sendpb(s,g,2,note,lf,lp);ack=0;continue
   if typ!=0x7f:raise RuntimeError(f'Pacchetto {typ}')
   lp=pkt;pending+=pl;ack+=1
   while len(pending)>=22:
    ft=struct.unpack_from('<H',pending,4)[0];fs=struct.unpack_from('<I',pending,18)[0]
    if len(pending)<22+fs:break
    lf=struct.unpack_from('<I',pending,0)[0];body=bytes(pending[22:22+fs]);del pending[:22+fs]
    if ft==22:
     if len(body)!=256 or body[2]>88 or body[3]!=0:raise RuntimeError('Formato audio type22 diverso dal campione IMA ADPCM validato; dati grezzi conservati')
     af.write(body);audio_blocks+=1
    if ft not in VIDEO:continue
    x=payload(body,k)
    if not x:continue
    if codec is None:
     idx=3 if len(x)>3 and x[2]==1 else 4;nal=x[idx]&31;codec='h264' if nal in (1,5,7,8) else 'hevc'
    f.write(x);video_frames+=1;written+=len(x);expected=max(900000,(g['end']-g['start'])*28000);STATE['progress_pct']=min(92,int(written*100/expected));STATE['progress']=f'Scaricati {written/1048576:.1f} MB'
   if ack>=200:sendpb(s,g,2,note,lf,lp);ack=0
 if not written:raise RuntimeError('Nessun video ricevuto')
 return codec or 'hevc',audio_path,audio_blocks,video_frames
def paths():
 c=cfg();base=Path(os.path.expanduser(c['save_dir']));return base,base/'Thumbnails'
def library():
 base,thumb=paths();base.mkdir(parents=True,exist_ok=True);thumb.mkdir(parents=True,exist_ok=True);items=[]
 names={p.stem:p for p in base.glob('V380_*.mp4') if not p.name.endswith('.partial.mp4')}
 gifs={p.stem:p for p in thumb.glob('V380_*.gif')}
 all_stems=sorted(set(names)|set(gifs))
 # Stable local numbering per calendar day, independent of pagination/current selected day.
 by_day={}
 for stem in all_stems:
  try:
   d=datetime.strptime(stem.replace('V380_','',1),'%Y-%m-%d_%H-%M-%S');by_day.setdefault(d.strftime('%Y-%m-%d'),[]).append((d,stem))
  except:pass
 ranks={}
 for day,vals in by_day.items():
  for n,(_,stem) in enumerate(sorted(vals),1):ranks[stem]=n
 for stem in all_stems:
  v=names.get(stem);gif=gifs.get(stem);m=library_meta(stem,v,gif,ranks.get(stem));items.append({'name':stem,'video':v.name if v else None,'thumb':gif.name if gif else None,'size':v.stat().st_size if v else 0,**m})
 return sorted(items,key=lambda x:x['name'],reverse=True)
def makegif(mp4,gif,duration):
 c=cfg();wanted=max(3,min(60,int(c.get('preview_frames',10))));total=max(1.0,min(60.0,float(c.get('preview_seconds',3))));start=max(0.0,float(c.get('preview_start',4)));end=max(start+0.5,float(c.get('preview_end',35)));end=min(float(duration),end);start=min(start,max(0.0,end-0.5));span=max(0.5,end-start);frame_count=max(1,min(wanted,int(span*10)))
 # Extract exactly frame_count stills, evenly distributed across the selected source interval.
 tmp=Path(str(gif)+'.frames');shutil.rmtree(tmp,ignore_errors=True);tmp.mkdir(parents=True,exist_ok=True)
 try:
  src_fps=frame_count/span
  extract=[ffmpeg(),'-y','-hide_banner','-loglevel','error','-ss',f'{start:.3f}','-t',f'{span:.3f}','-i',str(mp4),'-vf',f'fps={src_fps:.9f},scale=480:-1:flags=lanczos','-frames:v',str(frame_count),str(tmp/'frame_%03d.png')]
  pe=subprocess.run(extract,capture_output=True)
  if pe.returncode:raise RuntimeError(pe.stderr.decode(errors='replace'))
  frames=sorted(tmp.glob('frame_*.png'))
  if not frames:raise RuntimeError('Nessun fotogramma estratto per anteprima')
  # GIF delay is centiseconds per frame: total seconds / actual number of frames.
  delay_cs=max(2,round(total*100/len(frames)))
  concat=tmp/'frames.txt'
  concat.write_text(''.join([f"file '{f.name}'\nduration {delay_cs/100:.2f}\n" for f in frames])+f"file '{frames[-1].name}'\n")
  pg=subprocess.run([ffmpeg(),'-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-vf','split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(gif)],cwd=str(tmp),capture_output=True)
  if pg.returncode:raise RuntimeError(pg.stderr.decode(errors='replace'))
  log(f'GIF OK frames={len(frames)} delay={delay_cs}cs total~={len(frames)*delay_cs/100:.2f}s interval={start:.1f}-{end:.1f}s')
 finally:shutil.rmtree(tmp,ignore_errors=True)
HTML="""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V380 Mac 3.14.15</title><style>
:root{--bg1:#150728;--bg2:#401067;--bg3:#1f0c39;--glass:rgba(255,255,255,.085);--line:rgba(255,255,255,.15);--muted:rgba(255,255,255,.7);--pink:#e747f5;--cyan:#20c9ff}*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display",sans-serif;color:#fff}body{background:radial-gradient(circle at 42% 35%,rgba(235,58,240,.27),transparent 28%),radial-gradient(circle at 86% 72%,rgba(81,50,255,.2),transparent 33%),linear-gradient(135deg,var(--bg1),var(--bg2) 50%,var(--bg3));background-attachment:fixed}.shell{min-height:100vh;display:grid;grid-template-columns:220px minmax(680px,1120px);justify-content:center;padding:18px;gap:16px}.glass{background:var(--glass);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);border:1px solid var(--line);box-shadow:0 16px 40px rgba(0,0,0,.26),inset 0 1px rgba(255,255,255,.08)}aside{border-radius:22px;padding:22px 14px;display:flex;flex-direction:column;height:max-content;min-height:560px;max-height:720px;position:sticky;top:18px;align-self:start}.brand{font-size:23px;font-weight:800;padding:18px 12px 26px}.brand .cam{color:#ff74ef;filter:drop-shadow(0 0 8px #ff42e6)}nav{display:grid;gap:8px}.nav{display:flex;gap:12px;align-items:center;width:100%;padding:12px 14px;border:1px solid transparent;border-radius:13px;color:#fff;background:transparent;font-size:16px;text-align:left;cursor:pointer}.nav:hover,.nav.active{background:rgba(255,255,255,.10);border-color:rgba(255,107,220,.48);box-shadow:0 0 18px rgba(236,72,255,.2)}.ico{width:20px;color:#f1a8ff}.exit{margin-top:18px;background:rgba(255,255,255,.18)}main{min-width:0;width:100%;max-width:1120px;padding:12px 6px 22px}.panel{border-radius:19px;padding:17px;margin-bottom:16px}.head{display:flex;align-items:center;margin-bottom:12px}.head h2{font-size:19px;margin:0;flex:1}.muted{color:var(--muted)}.row{display:flex;align-items:center;gap:9px;flex-wrap:wrap}input,select{color:#fff;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:9px 11px;outline:none}.pill{border:1px solid rgba(255,255,255,.13);border-radius:999px;padding:8px 13px;color:#fff;background:rgba(255,255,255,.10);cursor:pointer}.pill:hover{background:rgba(255,255,255,.17)}.primary{border:0;background:linear-gradient(135deg,var(--pink),#a125c1 57%,var(--cyan));box-shadow:0 4px 15px rgba(224,64,251,.38);font-weight:700}.danger{background:rgba(239,68,68,.24);border-color:rgba(255,86,86,.37)}.statusrow{display:flex;align-items:center;margin:11px 0 3px}.statusrow #status{flex:1}.refresh{width:34px;height:34px;padding:0;font-size:19px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;table-layout:fixed}th:nth-child(1),td:nth-child(1){width:8%}th:nth-child(2),td:nth-child(2){width:28%}th:nth-child(3),td:nth-child(3){width:28%}th:nth-child(4),td:nth-child(4){width:36%;text-align:left}.progressBadge{min-width:92px;text-align:center;display:inline-block}th,td{padding:10px 7px;text-align:left;border-bottom:1px solid rgba(255,255,255,.08);white-space:nowrap}th{font-size:12px;color:rgba(255,255,255,.76)}tbody tr:hover{background:rgba(255,255,255,.07)}tbody tr.downloaded{background:rgba(54,214,124,.12)}tbody tr.previewonly{background:rgba(255,195,67,.10)}.badge{display:inline-block;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:700}.ok{color:#a5f4bf;background:rgba(43,193,104,.18)}.prev{color:#ffdc8b;background:rgba(255,184,43,.16)}.library{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}.libraryPager{display:flex;align-items:center;justify-content:center;gap:10px;margin-top:16px}.pageInfo{color:var(--muted);font-size:12px}.tile{padding:10px;border-radius:16px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);box-shadow:0 8px 22px rgba(0,0,0,.17)}.thumb,.thumbph{width:100%;height:165px;object-fit:cover;border-radius:12px;background:rgba(11,6,28,.72);display:grid;place-items:center;color:var(--muted)}.tile h3{font-size:13px;margin:9px 2px 3px;overflow:hidden;text-overflow:ellipsis}.tile p{font-size:12px;margin:0 2px 9px}.actions{display:grid;grid-template-columns:1fr 1fr;gap:7px}.metaBar{display:flex;align-items:center;justify-content:space-between;margin:8px 2px 2px}.iconBtn{width:33px;height:33px;border-radius:50%;display:grid;place-items:center;border:1px solid rgba(255,255,255,.17);background:rgba(255,255,255,.08);color:#fff;cursor:pointer;font-weight:800}.mediaState{width:13px;height:13px;border-radius:50%;display:inline-block}.mediaState.ok{background:#56ef8a;box-shadow:0 0 10px rgba(86,239,138,.8)}.mediaState.missing{background:#ff5467;box-shadow:0 0 10px rgba(255,84,103,.8)}.thumb{cursor:pointer}.thumb:hover{filter:brightness(1.08);outline:2px solid rgba(240,90,255,.55)}dialog.mediaPanel{width:min(560px,88vw);max-height:78vh;overflow:auto;padding:0;border:1px solid var(--line);border-radius:20px;color:#fff;background:rgba(35,13,57,.95);backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);box-shadow:0 25px 70px rgba(0,0,0,.45)}dialog.mediaPanel::backdrop{background:rgba(8,2,17,.65);backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px)}.mediaCard{padding:20px;border-radius:20px;background:transparent}.mediaActions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px}.infoGrid{display:grid;grid-template-columns:110px 1fr;gap:7px 12px;font-size:13px}.infoGrid b{color:rgba(255,255,255,.62)}.inlineConfirm{display:none;margin-top:14px;padding:13px;border-radius:14px;background:rgba(239,68,68,.13);border:1px solid rgba(255,90,90,.28)}.inlineConfirm.show{display:block}.confirmText{font-size:13px;margin-bottom:10px;color:rgba(255,255,255,.82)}.actions .pill{font-size:12px;padding:7px 8px}.open{background:linear-gradient(135deg,#a737e9,#24bdf4);border:0}.empty{color:var(--muted);padding:25px;text-align:center}dialog{width:min(580px,92vw);border:1px solid var(--line);border-radius:20px;color:#fff;background:rgba(35,13,57,.95);backdrop-filter:blur(26px);box-shadow:0 25px 70px rgba(0,0,0,.45)}dialog::backdrop{background:rgba(8,2,17,.62);backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px)}.settingsgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.settingsgrid label{display:grid;gap:5px;font-size:13px;color:var(--muted)}.wide{grid-column:1/-1}.connled{width:20px;height:20px;border-radius:50%;display:inline-block;margin-left:8px;vertical-align:-3px;border:2px solid rgba(255,255,255,.7);background:#e35ad7;box-shadow:0 0 14px rgba(227,90,215,.8)}.connled.ok{background:#36d476;box-shadow:0 0 14px rgba(54,212,118,.95)}.connled.bad{background:#ff4b5c;box-shadow:0 0 14px rgba(255,75,92,.95);animation:blink 1s infinite}@keyframes blink{50%{opacity:.2;box-shadow:none}}.refreshIcon{width:38px;height:38px;border-radius:50%;padding:0;font-size:23px;background:radial-gradient(circle at 35% 25%,rgba(255,255,255,.28),rgba(255,255,255,.07));border:1px solid rgba(243,165,255,.38);box-shadow:0 0 16px rgba(219,78,244,.25);display:grid;place-items:center}.refreshIcon:hover{transform:rotate(45deg);transition:.2s;background:rgba(255,255,255,.16)}.refreshIcon{overflow:hidden;border:1px solid rgba(255,255,255,.26)!important;background:transparent!important}.refreshIcon img{width:100%;height:100%;object-fit:cover;border-radius:50%;transition:transform .55s ease,filter .3s ease}.refreshIcon:hover img{transform:rotate(180deg);filter:hue-rotate(72deg) saturate(1.45) brightness(1.15)}.refreshIcon.busy img{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.rowprogress{position:relative;overflow:hidden}.rowprogress::before{content:'';position:absolute;inset:0 auto 0 0;width:var(--pct,0%);background:linear-gradient(90deg,rgba(35,190,91,.20),rgba(49,232,118,.48));transition:width .45s ease}.rowprogress td{position:relative}.progressBadge{position:relative;overflow:hidden;background:rgba(255,255,255,.10)}.progressBadge::before{content:'';position:absolute;inset:0 auto 0 0;width:var(--pct,0%);background:linear-gradient(90deg,#27bf62,#72ef9a);transition:width .45s ease}.progressBadge span{position:relative;z-index:1}.frameCount{font-variant-numeric:tabular-nums}.timelineBox{margin:14px 0 18px;padding:14px 14px 10px;border-radius:15px;background:rgba(10,5,28,.32);border:1px solid rgba(255,255,255,.10)}.timelineHead{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;color:var(--muted);font-size:12px}.timeline{position:relative;height:58px;margin:0 8px}.timelineRail{position:absolute;left:0;right:0;top:24px;height:4px;border-radius:99px;background:linear-gradient(90deg,rgba(255,255,255,.14),rgba(255,255,255,.32),rgba(255,255,255,.14))}.timelineTicks{position:absolute;left:0;right:0;top:34px;display:flex;justify-content:space-between;color:rgba(255,255,255,.55);font-size:10px}.eventMark{position:absolute;top:13px;width:14px;height:25px;transform:translateX(-50%);border:0;border-radius:6px;background:linear-gradient(180deg,#f15bff,#29c9ff);box-shadow:0 0 12px rgba(224,64,251,.65);cursor:pointer;padding:0}.eventMark:hover,.eventMark.active{height:32px;top:9px;filter:brightness(1.25);box-shadow:0 0 18px rgba(70,218,255,.95)}.eventMark.downloaded{background:linear-gradient(180deg,#74f59b,#28b960)}.eventMark.preview{background:linear-gradient(180deg,#ffd86b,#d99d14)}.brandButton{border:0;background:transparent;color:#fff;font:inherit;font-weight:800;padding:0;cursor:pointer;text-align:left}.brandButton:hover{text-shadow:0 0 12px rgba(255,255,255,.5)}.folderRow{display:grid;grid-template-columns:1fr auto;gap:8px}.miniOpen{align-self:end;margin-bottom:1px}.cameraNameHint{font-size:11px;color:var(--muted);margin-top:5px}.settingsShell{padding:6px}.settingSection{margin:14px 0;padding:16px;border-radius:17px;background:linear-gradient(135deg,rgba(55,170,80,.16),rgba(28,95,45,.22));border:1px solid rgba(111,238,133,.28);box-shadow:inset 0 1px rgba(255,255,255,.07),0 8px 22px rgba(8,70,23,.13)}.settingTitle{display:flex;align-items:center;gap:9px;margin:0 0 13px;font-size:15px;color:#d8ffd9;font-weight:750}.settingDot{width:10px;height:10px;border-radius:50%;background:#70ef84;box-shadow:0 0 12px rgba(112,239,132,.75)}.settingSection input,.settingSection select{background:rgba(255,255,255,.10);border-color:rgba(174,255,184,.18)}.settingSection input:focus,.settingSection select:focus{border-color:#70ef84;box-shadow:0 0 0 3px rgba(112,239,132,.13)}.defaultBtn{background:rgba(80,198,99,.18);border-color:rgba(112,239,132,.35);color:#dfffe3}.defaultBtn:hover{background:rgba(90,210,110,.28)}@media(max-width:800px){.shell{grid-template-columns:1fr;padding:10px}aside{min-height:auto}.exit{margin-top:10px}main{padding:0}.settingsgrid{grid-template-columns:1fr}.wide{grid-column:auto}}

:root{--theme-a:#150728;--theme-b:#401067;--theme-c:#1f0c39;--accent:#e747f5;--accent2:#20c9ff;--glow:rgba(235,58,240,.24);--dialog-bg:rgba(35,13,57,.96)}
body[data-palette="green"]{--theme-a:#06230d;--theme-b:#17562b;--theme-c:#002b16;--accent:#83d548;--accent2:#28c77d;--glow:rgba(121,225,68,.27);--dialog-bg:rgba(8,40,22,.96)}
body[data-palette="magenta"]{--theme-a:#350424;--theme-b:#7d125d;--theme-c:#3b0629;--accent:#f558cf;--accent2:#bd45c9;--glow:rgba(255,73,203,.25);--dialog-bg:rgba(55,8,43,.96)}
body[data-palette="orange"]{--theme-a:#401205;--theme-b:#94400d;--theme-c:#4b1705;--accent:#ffba50;--accent2:#f2762a;--glow:rgba(255,167,47,.26);--dialog-bg:rgba(65,24,8,.96)}
body[data-palette="blue"]{--theme-a:#041b3e;--theme-b:#163d82;--theme-c:#27105b;--accent:#49c9ff;--accent2:#8263ed;--glow:rgba(45,171,255,.25);--dialog-bg:rgba(7,26,60,.96)}
body[data-palette="teal"]{--theme-a:#032e32;--theme-b:#086e70;--theme-c:#003c3b;--accent:#5de0d1;--accent2:#1aa9bf;--glow:rgba(54,225,205,.25);--dialog-bg:rgba(4,43,46,.96)}
body{background:radial-gradient(circle at 42% 35%,var(--glow),transparent 40%),linear-gradient(135deg,var(--theme-a),var(--theme-b) 50%,var(--theme-c));background-attachment:fixed;--pink:var(--accent);--cyan:var(--accent2)}
.primary,.actions .open,.pill.open{background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 4px 15px var(--glow)}
.nav.active,.nav:hover{border-color:var(--accent);box-shadow:0 0 18px var(--glow)}.ico{color:var(--accent)}
dialog,dialog.mediaPanel{background:var(--dialog-bg)}.settingSection{background:rgba(255,255,255,.06);border-color:var(--accent)}.settingDot{background:var(--accent);box-shadow:0 0 12px var(--glow)}
.eventMark{background:linear-gradient(180deg,var(--accent),var(--accent2))}.eventMark.downloaded{background:linear-gradient(180deg,#74f59b,#28b960)}
#connled{background:#e5b64a!important;box-shadow:0 0 14px rgba(229,182,74,.7)!important}
#connled.ok{background:#36d476!important;box-shadow:0 0 14px rgba(54,212,118,.95)!important;animation:none!important}
#connled.bad{background:#ff4b5c!important;box-shadow:0 0 14px rgba(255,75,92,.95)!important}
.library{grid-template-columns:repeat(3,minmax(0,1fr))}.galleryFilters label{font-size:13px}.galleryFilters select{margin-left:7px}.galleryFilters input[type=checkbox]{width:auto}
@media(max-width:1000px){.library{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.library{grid-template-columns:1fr}}
</style></head><body><div class="shell"><aside class="glass"><div class="brand"><button id="brandName" class="brandButton" onclick="settings.showModal()">Ingresso</button> <span id="connled" class="connled" title="Verifica connessione"></span><div class="cameraNameHint">V380 Mac 3.14.15</div></div><nav><button class="nav active" onclick="recordings.scrollIntoView({behavior:'smooth'})"><span class="ico">▣</span>Registrazioni</button><button class="nav" onclick="library.scrollIntoView({behavior:'smooth'})"><span class="ico">▱</span>Gallery</button><button class="nav" onclick="settings.showModal()"><span class="ico">⚙</span>Impostazioni</button></nav><button class="nav exit" onclick="quitApp()">Esci</button></aside><main><section id="recordings" class="panel glass"><div class="head"><h2>Scarica video</h2></div><div class="row"><button class="pill" title="Giorno precedente" onclick="shiftDay(-1)">‹</button><input id="day" type="date"><button type="button" class="pill primary" onclick="downloadWholeDay()">Scarica giornata</button><button type="button" class="pill" onclick="stopQueue()">Ferma coda</button><button class="pill" title="Giorno successivo" onclick="shiftDay(1)">›</button><button id="down" class="pill primary" disabled onclick="downloadRec()">Scarica video</button></div><div class="statusrow"><span id="status" class="muted">Pronto.</span><button id="refreshBtn" class="refreshIcon" title="Aggiorna registrazioni e libreria" onclick="refreshAll()"><img src="/assets/refresh.jpg" alt="Aggiorna"></button></div><div class="timelineBox"><div class="timelineHead"><span>Distribuzione giornaliera</span><span>00:00 → 23:59</span></div><div class="timeline"><div class="timelineRail"></div><div id="timelineEvents"></div><div class="timelineTicks"><span>00</span><span>04</span><span>08</span><span>12</span><span>16</span><span>20</span><span>24</span></div></div></div><div class="tablewrap"><table><thead><tr><th>#</th><th>Inizio</th><th>Fine</th><th>Stato</th></tr></thead><tbody id="rows"></tbody></table></div></section><section id="library" class="panel glass"><div class="head"><h2>Gallery</h2></div><div class="row" style="margin-bottom:12px"><button type="button" class="pill" onclick="selectPageVideos()">Seleziona video pagina</button><button type="button" class="pill" onclick="clearVideoSelection()">Deseleziona</button><button type="button" class="pill danger" onclick="askBulkTrash()">Cestina selezionati</button><span id="bulkCount" aria-live="polite">0 selezionati</span></div><div class="row galleryFilters" style="margin-bottom:14px"><label>Elementi per pagina <select id="library_page_size" onchange="galleryOptionsChanged()"><option>6</option><option selected>12</option><option>18</option><option>24</option><option>30</option><option>36</option><option>48</option><option>60</option><option value="all">Tutti</option></select></label><label style="display:flex;align-items:center;gap:8px"><input id="gallery_day_only" type="checkbox" onchange="galleryOptionsChanged()">Mostra solo il giorno selezionato</label><span id="galleryDayLabel" class="muted"></span></div><div id="gallery" class="library"></div><div id="libraryPager" class="libraryPager"></div></section></main></div><dialog id="settings"><form class="settingsShell" onsubmit="save(event)"><div class="head"><h2>Impostazioni</h2></div><section class="settingSection"><div class="settingTitle"><span class="settingDot"></span>Telecamera</div><div class="settingsgrid"><label class="wide">Nome telecamera<input id="camera_name" maxlength="40" placeholder="es. Ingresso"></label><label>IP telecamera<input id="host"></label><label>Porta<input id="port" type="number"></label><label>Device ID<input id="device_id"></label><label>Username<input id="username"></label><label class="wide">Password Portachiavi<input id="password" type="password" placeholder="Vuoto = non cambiare"></label></div></section><section class="settingSection"><div class="settingTitle"><span class="settingDot"></span>Anteprima <button type="button" class="pill defaultBtn" style="margin-left:auto" onclick="previewDefaults()">Default</button></div><div class="settingsgrid"><label>Fotogrammi anteprima<input id="preview_frames" type="number" min="3" max="60"></label><label>Durata anteprima (secondi)<input id="preview_seconds" type="number" min="1" max="60" step="0.5"></label><label>Inizio intervallo video (secondo)<input id="preview_start" type="number" min="0" max="600" step="1"></label><label>Fine intervallo video (secondo)<input id="preview_end" type="number" min="1" max="600" step="1"></label></div></section><section class="settingSection"><div class="settingTitle"><span class="settingDot"></span>Altro</div><div class="settingsgrid"><label class="wide">Cartella video<input id="save_dir"></label><label>Palette colori<select id="palette" onchange="paletteChanged(this.value)"><option value="purple">Viola originale</option><option value="green">Verde bosco</option><option value="magenta">Magenta</option><option value="orange">Arancio ambra</option><option value="blue">Blu indaco</option><option value="teal">Turchese petrolio</option></select></label><label>Player video<select id="player"><option value="VLC">VLC</option><option value="IINA">IINA</option><option value="QuickTime Player">QuickTime Player</option><option value="default">Predefinito macOS</option></select></label><label>Lingua<select id="language"><option value="it">Italiano</option><option value="en">English</option></select></label><label class="wide" style="display:flex;grid-template-columns:auto 1fr;align-items:center;gap:9px"><input id="time_correction" type="checkbox" style="width:auto" checked><span>Correzione ora video (-1 ora)</span></label></div></section><div class="row" style="justify-content:flex-end;margin-top:18px"><button type="button" class="pill" onclick="settings.close()">Annulla</button><button class="pill primary">Salva</button></div></form></dialog><dialog id="mediaPanel" class="mediaPanel"><div class="mediaCard"><div class="head"><h2 id="mediaTitle">Video</h2><button class="pill" onclick="closeMediaPanel()">Chiudi</button></div><div id="mediaInfo" class="infoGrid"></div><div id="mediaActions" class="mediaActions"></div><div id="inlineConfirm" class="inlineConfirm"><div id="confirmText" class="confirmText"></div><div class="row" style="justify-content:flex-end"><button class="pill" onclick="cancelInlineDelete()">Annulla</button><button id="confirmDeleteBtn" class="pill danger">Elimina</button></div></div></div></dialog><script>const brandName=document.getElementById("brandName"),connled=document.getElementById("connled"),recordings=document.getElementById("recordings"),day=document.getElementById("day"),down=document.getElementById("down"),status=document.getElementById("status"),refreshBtn=document.getElementById("refreshBtn"),timelineEvents=document.getElementById("timelineEvents"),rows=document.getElementById("rows"),library=document.getElementById("library"),gallery=document.getElementById("gallery"),libraryPager=document.getElementById("libraryPager"),settings=document.getElementById("settings"),camera_name=document.getElementById("camera_name"),host=document.getElementById("host"),port=document.getElementById("port"),device_id=document.getElementById("device_id"),username=document.getElementById("username"),password=document.getElementById("password"),preview_frames=document.getElementById("preview_frames"),preview_seconds=document.getElementById("preview_seconds"),preview_start=document.getElementById("preview_start"),preview_end=document.getElementById("preview_end"),save_dir=document.getElementById("save_dir"),player=document.getElementById("player"),language=document.getElementById("language"),library_page_size=document.getElementById("library_page_size"),time_correction=document.getElementById("time_correction"),mediaPanel=document.getElementById("mediaPanel"),mediaTitle=document.getElementById("mediaTitle"),mediaInfo=document.getElementById("mediaInfo"),mediaActions=document.getElementById("mediaActions"),inlineConfirm=document.getElementById("inlineConfirm"),confirmText=document.getElementById("confirmText"),confirmDeleteBtn=document.getElementById("confirmDeleteBtn");

let I18N={"it": {"recordings": "Registrazioni", "gallery": "Gallery", "settings": "Impostazioni", "exit": "Esci", "download_video": "Scarica video", "ready": "Pronto.", "daily_distribution": "Distribuzione giornaliera", "start": "Inizio", "end": "Fine", "status": "Stato", "download": "Scarica", "downloaded": "Scaricato", "preview": "Anteprima", "refresh": "Aggiorna", "camera": "Telecamera", "camera_name": "Nome telecamera", "camera_ip": "IP telecamera", "port": "Porta", "device_id": "Device ID", "username": "Username", "keychain_password": "Password Portachiavi", "password_hint": "Vuoto = non cambiare", "preview_frames": "Fotogrammi anteprima", "preview_duration": "Durata anteprima (secondi)", "preview_start": "Inizio intervallo video (secondo)", "preview_end": "Fine intervallo video (secondo)", "default": "Default", "other": "Altro", "video_folder": "Cartella video", "video_player": "Player video", "library_page": "Elementi Libreria per pagina", "time_correction": "Correzione ora video (-1 ora)", "language": "Lingua", "cancel": "Annulla", "save": "Salva", "close": "Chiudi", "open_video": "Apri video", "delete_video": "Elimina video", "open_preview": "Anteprima", "delete_preview": "Elimina anteprima", "info": "Informazioni", "file_name": "Nome file", "date": "Data", "time": "Orario", "path": "Percorso", "size": "Dimensione", "present": "Presente", "missing": "Assente", "video_present": "Video presente", "video_missing": "Video non presente", "only_preview": "Solo anteprima", "video_saved": "Video salvato", "hover_preview": "Passa il mouse per creare anteprima", "creating_preview": "Creo anteprima\u2026", "delete_video_confirm": "Eliminare questo video dal Mac? L\u2019anteprima rester\u00e0 disponibile.", "delete_preview_confirm": "Eliminare definitivamente questa anteprima?", "delete": "Elimina", "saved_settings": "\u2713 Impostazioni salvate", "connection": "Connessione\u2026", "no_saved_videos": "Nessun video salvato.", "page": "Pagina", "of": "di", "items": "elementi", "redownload": "Scarica nuovamente", "open": "Apri", "default_player": "Predefinito macOS", "error_preview": "Errore anteprima", "removed": "MP4 eliminato", "closed": "V380 Mac chiuso", "close_tab": "Puoi chiudere questa scheda.", "previous_day": "Giorno precedente", "next_day": "Giorno successivo", "refresh_all": "Aggiorna registrazioni e libreria"}, "en": {"recordings": "Recordings", "gallery": "Gallery", "settings": "Settings", "exit": "Quit", "download_video": "Download video", "ready": "Ready.", "daily_distribution": "Daily distribution", "start": "Start", "end": "End", "status": "Status", "download": "Download", "downloaded": "Downloaded", "preview": "Preview", "refresh": "Refresh", "camera": "Camera", "camera_name": "Camera name", "camera_ip": "Camera IP", "port": "Port", "device_id": "Device ID", "username": "Username", "keychain_password": "Keychain password", "password_hint": "Empty = keep unchanged", "preview_frames": "Preview frames", "preview_duration": "Preview duration (seconds)", "preview_start": "Video interval start (second)", "preview_end": "Video interval end (second)", "default": "Default", "other": "Other", "video_folder": "Video folder", "video_player": "Video player", "library_page": "Gallery items per page", "time_correction": "Video time correction (-1 hour)", "language": "Language", "cancel": "Cancel", "save": "Save", "close": "Close", "open_video": "Open video", "delete_video": "Delete video", "open_preview": "Preview", "delete_preview": "Delete preview", "info": "Information", "file_name": "File name", "date": "Date", "time": "Time", "path": "Path", "size": "Size", "present": "Present", "missing": "Missing", "video_present": "Video present", "video_missing": "Video missing", "only_preview": "Preview only", "video_saved": "Video saved", "hover_preview": "Hover to create preview", "creating_preview": "Creating preview\u2026", "delete_video_confirm": "Delete this video from the Mac? The preview will remain available.", "delete_preview_confirm": "Permanently delete this preview?", "delete": "Delete", "saved_settings": "\u2713 Settings saved", "connection": "Connecting\u2026", "no_saved_videos": "No saved videos.", "page": "Page", "of": "of", "items": "items", "redownload": "Download again", "open": "Open", "default_player": "macOS default", "error_preview": "Preview error", "removed": "MP4 deleted", "closed": "V380 Mac closed", "close_tab": "You can close this tab.", "previous_day": "Previous day", "next_day": "Next day", "refresh_all": "Refresh recordings and gallery"}},LANG='it';
function tx(k){return (I18N[LANG]&&I18N[LANG][k])||(I18N.it&&I18N.it[k])||k}
const translatedNodes=new WeakMap(),translatedAttrs=new WeakMap();
function translatedText(value){
 const text=value.trim();let key=Object.keys(I18N.it).find(k=>I18N.it[k]===text);
 if(key)return value.replace(text,tx(key));
 if(LANG==='en')return value.replace(/([0-9]+) registrazioni/g,'$1 recordings').replace(/([0-9]+) scaricate/g,'$1 downloaded').replace(/([0-9]+) anteprime/g,'$1 previews').replace(/Pagina ([0-9]+) di ([0-9]+) · ([0-9]+) elementi/g,'Page $1 of $2 · $3 items');
 return value;
}
function translateUI(){
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;
 while(node=walker.nextNode()){
  if(node.parentElement.closest('script,style,#brandName,#mediaTitle,input,option[value="it"],option[value="en"]'))continue;
  let old=translatedNodes.get(node),source=old&&node.nodeValue===old.output?old.source:node.nodeValue;
  let output=translatedText(source);translatedNodes.set(node,{source,output});if(node.nodeValue!==output)node.nodeValue=output;
 }
 document.querySelectorAll('[title],[placeholder],[alt]').forEach(el=>{
  if(el.id==='brandName'||el.id==='camera_name'||el.closest('#gallery')&&el.tagName==='IMG')return;
  let saved=translatedAttrs.get(el)||{};
  ['title','placeholder','alt'].forEach(attr=>{if(!el.hasAttribute(attr))return;let value=el.getAttribute(attr),old=saved[attr],source=old&&value===old.output?old.source:value,output=translatedText(source);saved[attr]={source,output};if(value!==output)el.setAttribute(attr,output)});translatedAttrs.set(el,saved);
 });
}
let translationObserver=new MutationObserver(()=>translateUI());
translationObserver.observe(document.body,{subtree:true,childList:true,characterData:true});
async function loadLanguage(code){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),3000);
 try{let r=await fetch('/assets/languages.json',{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error('HTTP '+r.status);let data=await r.json();if(!data.it||!data.en)throw Error('Invalid language file');I18N=data}catch(e){console.warn('Language file unavailable; bundled translations used',e)}finally{clearTimeout(timer)}
 LANG=code==='en'?'en':'it';document.documentElement.lang=LANG;translateUI();
}
const chosenVideos=new Set();function updateBulkCount(){let e=document.getElementById('bulkCount');if(e)e.textContent=chosenVideos.size+' selezionati'}function selectPageVideos(){let size=galleryPageSize();filteredLibrary().slice((libraryPage-1)*size,libraryPage*size).forEach(x=>{if(x.video)chosenVideos.add(x.video)});renderLibrary();updateBulkCount()}function clearVideoSelection(){chosenVideos.clear();renderLibrary();updateBulkCount()}function batchPrompt(title,message,action){document.getElementById('batchTitle').textContent=title;document.getElementById('batchMessage').textContent=message;document.getElementById('batchConfirm').onclick=async()=>{document.getElementById('batchDialog').close();try{await action()}catch(e){alert(e.message)}};document.getElementById('batchDialog').showModal()}function downloadWholeDay(){batchPrompt('Scarica giornata','Scaricare tutte le registrazioni della data selezionata? I video gia presenti saranno saltati. La coda procede un file alla volta.',async()=>{await api('/api/download-day',{});poll()})}async function stopQueue(){await api('/api/stop-queue',{});alert('La coda si fermera dopo il file in corso.')}function askBulkTrash(){let names=[...chosenVideos];if(!names.length){alert('Seleziona almeno un video');return}batchPrompt('Cestina video selezionati','Spostare '+names.length+' MP4 locali nel Cestino del Mac? Le GIF restano. Nessun file sulla telecamera viene cancellato.',async()=>{let r=await api('/api/trash-many',{names});chosenVideos.clear();await lib();await loadRec();updateBulkCount();alert(r.moved+' video spostati nel Cestino')})}function normalizedPageSize(v){if(String(v)==='all')return 'all';let n=Number(v);return [6,12,18,24,30,36,48,60].includes(n)?n:12}function filteredLibrary(){if(!document.getElementById('gallery_day_only').checked)return libraryItems;let target=document.getElementById('day').value;return libraryItems.filter(x=>{let d=(x.date||'').split('-');let iso=d.length===3?[d[2],d[1],d[0]].join('-'):x.name.slice(5,15);return iso===target})}function galleryPageSize(){let v=document.getElementById('library_page_size').value;return v==='all'?Math.max(1,filteredLibrary().length):Number(v)||12}async function galleryOptionsChanged(){libraryPage=1;renderLibrary();updateBulkCount();try{await api('/api/ui-preferences',{library_page_size:document.getElementById('library_page_size').value,gallery_day_only:document.getElementById('gallery_day_only').checked})}catch(e){alert('Preferenze Gallery: '+e.message)}}function applyPalette(v){document.body.dataset.palette=['purple','green','magenta','orange','blue','teal'].includes(v)?v:'purple'}async function paletteChanged(v){applyPalette(v);try{await api('/api/ui-preferences',{palette:v})}catch(e){alert('Palette non salvata: '+e.message)}}let selected=null;day.value=localDay(new Date());day.addEventListener('change',()=>loadRec());async function api(p,b){let r=await fetch(p,{method:b?'POST':'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):null});let j=await r.json();if(!r.ok)throw Error(j.error||'Errore');return j}function localDay(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')}function shiftDay(delta){let d=new Date(day.value+'T12:00:00');d.setDate(d.getDate()+delta);day.value=localDay(d);loadRec()}async function testLogin(){let led=document.getElementById('connled');led.className='connled';led.title='Connessione in verifica…';try{let r=await api('/api/test-login');if(r.ok){led.className='connled ok';led.title='Telecamera connessa · login OK'}else{led.className='connled bad';led.title='Telecamera non raggiungibile: '+(r.error||'login fallito')}}catch(e){led.className='connled bad';led.title='Telecamera non raggiungibile: '+e.message}}function previewDefaults(){preview_frames.value=50;preview_seconds.value=10;preview_start.value=10;preview_end.value=60;}async function init(){let c=await api('/api/config');let setv=(id,v)=>{let e=document.getElementById(id);if(e)e.value=v};setv('host',c.host);setv('port',c.port);setv('device_id',c.device_id);setv('username',c.username);setv('save_dir',c.save_dir);setv('camera_name',c.camera_name||'Ingresso');document.getElementById('brandName').textContent=c.camera_name||'Ingresso';setv('player',c.player||'VLC');setv('language',c.language||'it');setv('library_page_size',normalizedPageSize(c.library_page_size));document.getElementById('gallery_day_only').checked=!!c.gallery_day_only;setv('palette',c.palette||'purple');applyPalette(c.palette||'purple');let tc=document.getElementById('time_correction');if(tc)tc.checked=c.time_correction!==false;setv('preview_frames',c.preview_frames??50);setv('preview_seconds',c.preview_seconds??10);setv('preview_start',c.preview_start??10);setv('preview_end',c.preview_end??60);await loadLanguage(c.language||'it');if(!c.has_password){document.getElementById('connled').className='connled bad';document.getElementById('settings').showModal()}else{await loadRec()}await lib()}async function refreshAll(){let b=document.getElementById('refreshBtn');b.classList.add('busy');try{await loadRec();await lib()}finally{b.classList.remove('busy')}}function renderTimeline(items){timelineEvents.innerHTML='';items.forEach((x,i)=>{let [h,m,sec]=x.start.split(':').map(Number);let pct=((h*3600+m*60+sec)/86400)*100;let b=document.createElement('button');b.className='eventMark'+(x.downloaded?' downloaded':(x.preview?' preview':''));b.style.left=pct+'%';b.title=x.start+'–'+x.end+(x.downloaded?' · Scaricato':(x.preview?' · Anteprima':''));b.onclick=()=>{let tr=rows.querySelector(`tr[data-index="${i}"]`);if(tr){document.querySelectorAll('.eventMark').forEach(e=>e.classList.remove('active'));b.classList.add('active');tr.click();if(!x.downloaded){let y=tr.getBoundingClientRect().top+window.scrollY-110;window.scrollTo({top:Math.max(0,y),behavior:'smooth'});tr.animate([{background:'rgba(50,210,255,.25)'},{background:'rgba(231,71,245,.20)'},{background:''}],{duration:1700});let btn=tr.querySelector('button');if(btn)btn.animate([{transform:'scale(1)'},{transform:'scale(1.13)',boxShadow:'0 0 22px rgba(63,220,255,.9)'},{transform:'scale(1)'}],{duration:1400})}}};timelineEvents.appendChild(b)})}async function loadRec(){try{status.textContent='Connessione…';let j=await api('/api/list',{day:day.value});let led=document.getElementById('connled');led.className='connled ok';led.title='Telecamera connessa - login e indice SD OK';rows.innerHTML='';j.items.forEach((x,i)=>{let tr=document.createElement('tr');tr.dataset.index=i;let stato=x.downloaded?'Scaricato':(x.preview?'Anteprima':'');tr.className=x.downloaded?'downloaded':(x.preview?'previewonly':'');let action=x.downloaded?`<span class="badge ok">${tx('downloaded')}</span>`:(x.preview?`<button class="pill prev" onclick="event.stopPropagation();downloadIndex(${i})">${tx('redownload')}</button>`:`<button class="pill primary" onclick="event.stopPropagation();downloadIndex(${i})">${tx('download')}</button>`);tr.innerHTML=`<td>${i+1}</td><td>${x.start}</td><td>${x.end}</td><td>${action}</td>`;tr.onclick=()=>{selected=i;down.disabled=!!x.downloaded;if(x.downloaded&&x.local_stem){focusLibrary(x.local_stem)}};rows.appendChild(tr)});renderTimeline(j.items);renderLibrary();translateUI();status.textContent=`${j.items.length} registrazioni · ${j.items.filter(x=>x.downloaded).length} scaricate · ${j.items.filter(x=>!x.downloaded&&x.preview).length} anteprime`}catch(e){connled.className='connled bad';console.error('SD list failed',e);status.textContent='Errore: '+e.message}}async function downloadIndex(i){selected=i;down.disabled=true;await api('/api/download',{index:i});poll()}async function downloadRec(){if(selected!==null)await downloadIndex(selected)}async function poll(){let j=await api('/api/status');status.textContent=j.error?'Errore: '+j.error:j.progress;let tr=j.active_index!==null?rows.querySelector(`tr[data-index="${j.active_index}"]`):null;if(tr){tr.classList.add('rowprogress');tr.style.setProperty('--pct',(j.progress_pct||0)+'%');let cell=tr.lastElementChild;if(cell)cell.innerHTML=`<span class="badge progressBadge" style="--pct:${j.progress_pct||0}%"><span>${j.progress_pct||0}%</span></span>`}if(j.busy)setTimeout(poll,450);else{loadRec();lib()}}let libraryPage=1,libraryItems=[];function renderLibrary(){gallery.innerHTML='';let visible=filteredLibrary();document.getElementById('galleryDayLabel').textContent=document.getElementById('gallery_day_only').checked?document.getElementById('day').value:'';let size=galleryPageSize(),pages=Math.max(1,Math.ceil(visible.length/size));libraryPage=Math.min(Math.max(1,libraryPage),pages);let subset=visible.slice((libraryPage-1)*size,libraryPage*size);if(!subset.length)gallery.innerHTML='<div class="empty">Nessun video salvato.</div>';subset.forEach(x=>{let d=document.createElement('article');d.className='tile';d.dataset.stem=x.name;d.innerHTML=`${x.thumb?`<img class="thumb" src="/media/thumb/${encodeURIComponent(x.thumb)}?t=${Date.now()}" onclick="openMediaPanel('${x.name}')">`:`<div class="thumbph" onclick="openMediaPanel('${x.name}')">Passa il mouse per creare anteprima</div>`}<h3>${x.label||x.name}</h3><p class="muted">${x.video?'Video salvato':'Solo anteprima'}</p><div class="metaBar"><button class="iconBtn" title="Informazioni" onclick="event.stopPropagation();showInfo('${x.name}')">i</button><span title="${x.video?'Video presente sul Mac':'Video non presente sul Mac'}" class="mediaState ${x.video?'ok':'missing'}"></span></div>`;if(x.video&&!x.thumb){let once=false;d.onmouseenter=async()=>{if(once)return;once=true;let ph=d.querySelector('.thumbph');if(ph)ph.textContent='Creo anteprima…';try{await api('/api/thumbnail',{name:x.video});await lib()}catch(e){if(ph)ph.textContent='Errore anteprima'}}}if(x.video){let label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:8px;margin:6px 0';let cb=document.createElement('input');cb.type='checkbox';cb.checked=chosenVideos.has(x.video);cb.onchange=()=>{if(cb.checked)chosenVideos.add(x.video);else chosenVideos.delete(x.video);updateBulkCount()};label.append(cb,document.createTextNode('Seleziona video'));d.prepend(label)}gallery.appendChild(d)});libraryPager.innerHTML=visible.length>size?`<button class="pill" ${libraryPage<=1?'disabled':''} onclick="libraryPage--;renderLibrary()">‹</button><span class="pageInfo">Pagina ${libraryPage} di ${pages} · ${visible.length} elementi</span><button class="pill" ${libraryPage>=pages?'disabled':''} onclick="libraryPage++;renderLibrary()">›</button>`:''}async function lib(){let j=await api('/api/library');libraryItems=j.items;renderLibrary()}function byName(n){return libraryItems.find(x=>x.name===n)}function showInfo(n){let x=byName(n);if(!x)return;mediaTitle.textContent=x.label||x.name;mediaInfo.innerHTML=`<b>Nome file</b><span>${x.filename||'MP4 eliminato'}</span><b>Data</b><span>${x.date||'-'}</span><b>Orario</b><span>${x.time||'-'}${x.end?' - '+x.end:''}</span><b>Percorso</b><span style="word-break:break-all">${x.path||'-'}</span><b>Dimensione</b><span>${x.size?(x.size/1048576).toFixed(1)+' MB':'-'}</span><b>Anteprima</b><span>${x.thumb?'Presente':'Assente'}</span>`;mediaActions.innerHTML='<button class="pill" onclick="closeMediaPanel()">OK</button>';if(!mediaPanel.open)mediaPanel.showModal()}function openMediaPanel(n){let x=byName(n);if(!x)return;mediaTitle.textContent=x.label||x.name;mediaInfo.innerHTML=`<b>Stato</b><span>${x.video?'Video presente':'Video non presente'}</span><b>Anteprima</b><span>${x.thumb?'Presente':'Assente'}</span>`;mediaActions.innerHTML=`${x.video?`<button class="pill open" onclick="openVideo('${x.video}')">Apri video</button><button class="pill danger" onclick="askDelete('video','${x.video}')">Elimina video</button>`:''}${x.thumb?`<button class="pill" onclick="openThumb('${x.thumb}')">Anteprima</button><button class="pill danger" onclick="askDelete('thumb','${x.thumb}')">Elimina anteprima</button>`:''}`;if(!mediaPanel.open)mediaPanel.showModal()}function closeMediaPanel(){cancelInlineDelete();if(mediaPanel.open)mediaPanel.close()}mediaPanel.addEventListener('click',e=>{let r=mediaPanel.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeMediaPanel()});async function focusLibrary(name){await lib();if(!filteredLibrary().some(x=>x.name===name))document.getElementById('gallery_day_only').checked=false;let size=galleryPageSize(),idx=filteredLibrary().findIndex(x=>x.name===name);if(idx<0)return;libraryPage=Math.floor(idx/size)+1;renderLibrary();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));let el=[...gallery.querySelectorAll('.tile')].find(e=>e.dataset.stem===name);if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.animate([{outline:'0 solid rgba(85,255,145,0)'},{outline:'6px solid rgba(85,255,145,.98)'},{outline:'6px solid rgba(85,255,145,.98)'},{outline:'0 solid rgba(85,255,145,0)'}],{duration:4000,easing:'ease-in-out'});}}
async function openVideo(n){await api('/api/open',{kind:'video',name:n})}async function openThumb(n){await api('/api/open',{kind:'thumb',name:n})}async function delVideo(n){await api('/api/delete',{name:n});await lib();await loadRec()}async function delThumb(n){await api('/api/delete-thumb',{name:n});await lib();await loadRec()}let pendingDelete=null;function askDelete(kind,name){pendingDelete={kind,name};confirmText.textContent=kind==='video'?'Eliminare questo video dal Mac? L’anteprima resterà disponibile.':'Eliminare definitivamente questa anteprima?';confirmDeleteBtn.onclick=confirmInlineDelete;inlineConfirm.classList.add('show')}function cancelInlineDelete(){pendingDelete=null;inlineConfirm.classList.remove('show')}async function confirmInlineDelete(){if(!pendingDelete)return;let x=pendingDelete;cancelInlineDelete();if(x.kind==='video')await delVideo(x.name);else await delThumb(x.name);closeMediaPanel()}async function folder(){await api('/api/folder')}async function quitApp(){await api('/api/quit',{});document.body.innerHTML='<main style="padding:40px"><section class="panel glass"><h2>V380 Mac chiuso</h2><p>Puoi chiudere questa scheda.</p></section></main>'}function nval(el,fallback){let n=Number(String(el.value).replace(',','.'));return Number.isFinite(n)?n:fallback}async function save(e){e.preventDefault();try{await api('/api/settings',{camera_name:camera_name.value.trim()||'Ingresso',host:host.value.trim(),port:nval(port,8800),device_id:nval(device_id,52405818),username:username.value.trim(),password:password.value,save_dir:save_dir.value.trim()||'~/Movies/V380',preview_frames:nval(preview_frames,50),preview_seconds:nval(preview_seconds,10),preview_start:nval(preview_start,10),preview_end:nval(preview_end,60),player:player.value,library_page_size:document.getElementById('library_page_size').value==='all'?'all':Number(document.getElementById('library_page_size').value),time_correction:time_correction.checked,language:document.getElementById('language').value});brandName.textContent=camera_name.value.trim()||'Ingresso';password.value='';settings.close();status.textContent='✓ Impostazioni salvate';await loadLanguage(document.getElementById('language').value);await loadRec();await lib()}catch(err){alert('Errore salvataggio: '+err.message)}}init().catch(err=>{console.error(err);status.textContent='Errore inizializzazione: '+err.message})</script><dialog id="batchDialog"><h2 id="batchTitle"></h2><p id="batchMessage"></p><div class="row"><button type="button" class="pill" onclick="document.getElementById('batchDialog').close()">Annulla</button><button type="button" class="pill primary" id="batchConfirm">Conferma</button></div></dialog></body></html>"""
def local_media_state(c,segment):
 base,thumb=paths()
 shown=datetime.fromtimestamp(segment.get('display_start',segment['start'])).strftime('%Y-%m-%d_%H-%M-%S')
 raw=datetime.fromtimestamp(segment['start']).strftime('%Y-%m-%d_%H-%M-%S')
 candidates=['V380_'+shown,'V380_'+raw]
 video=next((base/(x+'.mp4') for x in candidates if (base/(x+'.mp4')).exists()),None)
 preview=next((thumb/(x+'.gif') for x in candidates if (thumb/(x+'.gif')).exists()),None)
 return video,preview
def segment_item(c,x):
 video,preview=local_media_state(c,x)
 return {'start':datetime.fromtimestamp(x.get('display_start',x['start'])).strftime('%H:%M:%S'),'end':datetime.fromtimestamp(x.get('display_end',x['end'])).strftime('%H:%M:%S'),'duration':x['end']-x['start'],'downloaded':bool(video),'preview':bool(preview),'local_stem':video.stem if video else (preview.stem if preview else None)}
def library_meta(stem,video,preview,local_number=None):
 path=video if video else preview; date_text=''; time_text=''; end_text=''; number=''
 try:
  d=datetime.strptime(stem.replace('V380_','',1),'%Y-%m-%d_%H-%M-%S');date_text=d.strftime('%d-%m-%Y');time_text=d.strftime('%H:%M:%S')
 except: pass
 for i,g in enumerate(STATE.get('segments',[]),1):
  shown=datetime.fromtimestamp(g.get('display_start',g['start']));raw=datetime.fromtimestamp(g['start'])
  if stem in ('V380_'+shown.strftime('%Y-%m-%d_%H-%M-%S'),'V380_'+raw.strftime('%Y-%m-%d_%H-%M-%S')):
   number=f'N.{i}';date_text=shown.strftime('%d-%m-%Y');time_text=shown.strftime('%H:%M:%S');end_text=datetime.fromtimestamp(g.get('display_end',g['end'])).strftime('%H:%M:%S');break
 if not number and local_number:number=f'N.{local_number}'
 label=(number+' ' if number else '')+('del: '+date_text if date_text else stem)+((' ore: '+time_text+(' - '+end_text if end_text else '')) if time_text else '')
 return {'label':label,'path':str(path) if path else '', 'filename':video.name if video else '', 'date':date_text,'time':time_text,'end':end_text,'number':number}
JOB_LOCK=threading.Lock()
STOP_JOB=threading.Event()
def wrap_ima(source,dest,blocks):
 data=Path(source).read_bytes()
 if len(data)!=blocks*256:raise RuntimeError('Dimensione blocchi IMA non coerente')
 fmt=struct.pack('<HHIIHHHH',17,1,8000,4055,256,4,2,505)
 def chunk(tag,body):return tag+struct.pack('<I',len(body))+body+(b'\0' if len(body)%2 else b'')
 body=b'WAVE'+chunk(b'fmt ',fmt)+chunk(b'fact',struct.pack('<I',blocks*505))+chunk(b'data',data)
 Path(dest).write_bytes(b'RIFF'+struct.pack('<I',len(body))+body)
def save_recording(c,g):
 base,_=paths();base.mkdir(parents=True,exist_ok=True)
 dt=datetime.fromtimestamp(g.get('display_start',g['start']));stem='V380_'+dt.strftime('%Y-%m-%d_%H-%M-%S')
 raw=base/(stem+'.h265');mp4=base/(stem+'.mp4');temp=base/(stem+'.partial.mp4');wav=base/(stem+'.ima.wav')
 t,_=login(c);codec,audio,blocks,frames=download(c,t,g,raw)
 STATE['progress']='Creazione MP4 con audio AAC...';STATE['progress_pct']=96
 duration=max(1,g['end']-g['start']);rate=frames/duration
 cmd=[ffmpeg(),'-y','-hide_banner','-loglevel','error','-fflags','+genpts','-r',str(rate),'-f','h264' if codec=='h264' else 'hevc','-i',str(raw)]
 if blocks:
  wrap_ima(audio,wav,blocks);cmd+=['-i',str(wav),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-ar','8000','-ac','1','-b:a','16k']
 else:cmd+=['-map','0:v:0','-c:v','copy']
 if codec!='h264':cmd+=['-tag:v','hvc1']
 cmd+=['-movflags','+faststart',str(temp)]
 r=subprocess.run(cmd,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 temp.replace(mp4)
 for f in (raw,audio,wav):f.unlink(missing_ok=True)
 log('MP4 AUDIO OK '+str(mp4)+' blocks='+str(blocks)+' video_frames='+str(frames)+' fps='+str(rate))
 return mp4
def begin_download(indices):
 if not JOB_LOCK.acquire(blocking=False):raise RuntimeError('Download gia in corso')
 try:
  snapshot=[(i,dict(STATE['segments'][i])) for i in indices];c=runtime();STOP_JOB.clear()
  STATE.update(busy=True,error='',progress='Preparazione coda...',active_index=None,progress_pct=0)
 except Exception:
  JOB_LOCK.release();raise
 def work():
  done=skipped=0;errors=[]
  try:
   for pos,(i,g) in enumerate(snapshot,1):
    if STOP_JOB.is_set():break
    STATE['active_index']=i;STATE['progress_pct']=0
    if local_media_state(c,g)[0]:skipped+=1;continue
    STATE['progress']='File %d/%d'%(pos,len(snapshot))
    try:save_recording(c,g);done+=1;STATE['progress_pct']=100
    except Exception as e:errors.append(str(e));log('DOWNLOAD ERROR '+repr(e))
   STATE['progress']='Coda terminata: %d scaricati, %d gia presenti, %d errori%s'%(done,skipped,len(errors),' (interrotta)' if STOP_JOB.is_set() else '')
   STATE['error']='; '.join(errors[:3])
  finally:
   STATE['busy']=False;STATE['active_index']=None;JOB_LOCK.release()
 threading.Thread(target=work,daemon=True).start()
def trash_videos(names):
 if STATE['busy']:raise RuntimeError('Attendere la fine dei download prima della cancellazione')
 base,_=paths();trash=Path.home()/'.Trash';trash.mkdir(exist_ok=True)
 moved=[]
 for name in names:
  if Path(name).name!=name or not name.startswith('V380_') or not name.endswith('.mp4'):raise RuntimeError('Nome file non valido')
  f=base/name
  if not f.is_file():continue
  dest=trash/name
  if dest.exists():dest=trash/(f.stem+'_'+secrets.token_hex(4)+'.mp4')
  shutil.move(str(f),str(dest));moved.append(name)
 return moved
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def j(self,o,c=200):b=json.dumps(o).encode();self.send_response(c);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def body(self):return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
 def do_GET(self):
  p=urlparse(self.path)
  if p.path=='/':b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  elif p.path=='/assets/languages.json':
   b=(Path(__file__).parent/'languages.json').read_bytes();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-cache');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  elif p.path=='/assets/refresh.jpg':
   b=(Path(__file__).parent/'refresh_icon.jpg').read_bytes();self.send_response(200);self.send_header('Content-Type','image/jpeg');self.send_header('Cache-Control','public,max-age=86400');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  elif p.path=='/api/config':d=cfg();d['has_password']=bool(pw());self.j(d)
  elif p.path=='/api/status':self.j({k:STATE[k] for k in ['busy','progress','error','active_index','progress_pct']})
  elif p.path=='/api/test-login':
   try:
    c=runtime();ticket,ver=login(c);self.j({'ok':True,'version':ver,'ticket':ticket})
   except Exception as e:self.j({'ok':False,'error':str(e)})
  elif p.path=='/api/library':self.j({'items':library()})
  elif p.path.startswith('/media/thumb/'):
   n=Path(unquote(p.path.split('/media/thumb/',1)[1])).name;f=paths()[1]/n
   if not f.exists():self.send_error(404);return
   b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','image/gif');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:self.j({'error':'Not found'},404)
 def do_POST(self):
  try:
   d=self.body()
   if self.path=='/api/settings':
    c=cfg();c.update({k:d[k] for k in ['camera_name','host','port','device_id','username','save_dir','preview_frames','preview_seconds','preview_start','preview_end','player','library_page_size','time_correction','language'] if k in d});CFG.parent.mkdir(parents=True,exist_ok=True);CFG.write_text(json.dumps(c,indent=2));os.chmod(CFG,0o600);log('SETTINGS SAVED')
    if d.get('password'):setpw(d['password'])
    self.j({'ok':1})
   elif self.path=='/api/ui-preferences':
    c=cfg()
    if 'library_page_size' in d:
     v=d['library_page_size']
     if str(v)!='all' and int(v) not in (6,12,18,24,30,36,48,60):raise RuntimeError('Dimensione pagina non valida')
     c['library_page_size']='all' if str(v)=='all' else int(v)
    if 'gallery_day_only' in d:c['gallery_day_only']=bool(d['gallery_day_only'])
    if 'palette' in d:
     if d['palette'] not in ('purple','green','magenta','orange','blue','teal'):raise RuntimeError('Palette non valida')
     c['palette']=d['palette']
    CFG.parent.mkdir(parents=True,exist_ok=True);CFG.write_text(json.dumps(c,indent=2));os.chmod(CFG,0o600);self.j({'ok':1})
   elif self.path=='/api/list':
    if STATE['busy']:raise RuntimeError('Attendere la coda o interromperla prima di cambiare data')
    c=runtime();t,v=login(c);g=listrec(c,t,d['day']);STATE['segments']=g;self.j({'version':v,'items':[segment_item(c,x) for x in g]})
   elif self.path=='/api/download':
    begin_download([int(d['index'])]);self.j({'ok':1})
   elif self.path=='/api/download-day':
    if not STATE['segments']:raise RuntimeError('Nessuna registrazione caricata')
    begin_download(list(range(len(STATE['segments']))));self.j({'ok':1})
   elif self.path=='/api/stop-queue':
    STOP_JOB.set();self.j({'ok':1})
   elif self.path=='/api/trash-many':
    names=d.get('names',[])
    if not isinstance(names,list) or len(names)>2000:raise RuntimeError('Selezione non valida')
    moved=trash_videos(names);self.j({'ok':1,'moved':len(moved)})
   elif self.path=='/api/thumbnail':
    name=Path(d['name']).name;base,thumb=paths();video=base/name
    if not video.exists() or video.suffix!='.mp4':raise RuntimeError('Video non presente sul Mac')
    gif=thumb/(video.stem+'.gif');thumb.mkdir(parents=True,exist_ok=True)
    # Determine actual duration through ffprobe if available; filename clips are usually 120s.
    duration=120.0
    probe=Path(ffmpeg()).with_name('ffprobe')
    if probe.exists():
     pr=subprocess.run([str(probe),'-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(video)],capture_output=True,text=True)
     try:duration=float(pr.stdout.strip())
     except:pass
    makegif(video,gif,duration);self.j({'ok':1,'thumb':gif.name})
   elif self.path=='/api/delete-thumb':
    f=paths()[1]/Path(d['name']).name
    if f.exists() and f.suffix=='.gif':f.unlink()
    self.j({'ok':1})
   elif self.path=='/api/delete':
    f=paths()[0]/Path(d['name']).name
    if f.exists() and f.suffix=='.mp4':f.unlink()
    self.j({'ok':1})
   elif self.path=='/api/open':
    base,thumb=paths();f=(base if d['kind']=='video' else thumb)/Path(d['name']).name
    if f.exists():
     if d['kind']=='video':
      player=cfg().get('player','VLC')
      if player=='default': subprocess.Popen(['/usr/bin/open',str(f)])
      else: subprocess.Popen(['/usr/bin/open','-a',player,str(f)])
     else: subprocess.Popen(['/usr/bin/open',str(f)])
    self.j({'ok':1})
   elif self.path=='/api/folder':
    base,_=paths();base=Path(os.path.expanduser(str(base))).resolve();base.mkdir(parents=True,exist_ok=True);esc=str(base).replace('\\','\\\\').replace('\"','\\\"');script=f'tell application \"Finder\"\nactivate\nopen POSIX file \"{esc}\"\nend tell';r=subprocess.run(['/usr/bin/osascript','-e',script],capture_output=True,text=True)
    if r.returncode:
     r2=subprocess.run(['/usr/bin/open',str(base)],capture_output=True,text=True)
     if r2.returncode:raise RuntimeError('Impossibile aprire Finder: '+(r.stderr.strip() or r2.stderr.strip() or str(base)))
    self.j({'ok':1,'path':str(base)})
   elif self.path=='/api/quit':self.j({'ok':1});threading.Timer(.2,self.server.shutdown).start()
   else:self.j({'error':'Not found'},404)
  except Exception as e:self.j({'error':str(e)},400)
def main():
 log('V380 Mac 3.14.15 avviato');log('CONFIG START '+json.dumps({k:v for k,v in cfg().items() if k not in ('password',)},ensure_ascii=False));s=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Timer(.5,lambda:webbrowser.open(f'http://127.0.0.1:{s.server_port}/')).start();s.serve_forever()
if __name__=='__main__':main()
