"""Local media only: bounded range responses, GIF posters, explicit trash plans.
Never connects to a camera. Never traverses directories recursively for cleanup.
"""
import os
import re
import secrets
import shutil
import subprocess
import threading
from pathlib import Path
from urllib.parse import unquote

STEM=r'V380_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'
POSTER_LOCK=threading.RLock()

def checked_file(directory,name,suffix):
    directory=Path(directory).expanduser().resolve()
    if not re.fullmatch(STEM+re.escape(suffix),name):raise ValueError('Nome file non valido')
    f=directory/name
    if f.is_symlink() or not f.is_file() or f.resolve().parent!=directory:raise ValueError('File non disponibile')
    return f

def send_file(handler,f,content_type):
    size=f.stat().st_size;start=0;end=size-1;status=200
    value=handler.headers.get('Range')
    if value:
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
        try:
            if not match or not any(match.groups()):raise ValueError()
            a,b=match.groups()
            if not a:
                count=int(b)
                if count<=0:raise ValueError()
                start=max(0,size-count)
            else:
                start=int(a);end=min(size-1,int(b)) if b else size-1
            if start>=size or start>end:raise ValueError()
            status=206
        except ValueError:
            handler.send_response(416);handler.send_header('Content-Range','bytes */'+str(size));handler.send_header('Content-Length','0');handler.end_headers();return
    handler.send_response(status);handler.send_header('Content-Type',content_type)
    handler.send_header('Accept-Ranges','bytes');handler.send_header('Cache-Control','no-store')
    handler.send_header('X-Content-Type-Options','nosniff')
    handler.send_header('Content-Length',str(max(0,end-start+1)))
    if status==206:handler.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    handler.end_headers()
    try:
        with f.open('rb') as stream:
            stream.seek(start);remaining=end-start+1
            while remaining>0:
                chunk=stream.read(min(256*1024,remaining))
                if not chunk:break
                handler.wfile.write(chunk);remaining-=len(chunk)
    except (BrokenPipeError,ConnectionResetError):pass

def serve_local(handler,paths,path):
    try:
        parts=path.split('/')
        if len(parts)!=5 or parts[3] not in ('video','thumb'):raise ValueError()
        video=parts[3]=='video';name=unquote(parts[4]);f=checked_file(paths[0 if video else 1],name,'.mp4' if video else '.gif')
        send_file(handler,f,'video/mp4' if video else 'image/gif')
    except (ValueError,OSError):handler.send_error(404)

def serve_poster(handler,paths,path,ffmpeg):
    try:
        name=unquote(path.split('/media/poster/',1)[1]);gif=checked_file(paths[1],name,'.gif')
        cache=gif.parent/'.posters';cache.mkdir(exist_ok=True)
        if cache.is_symlink():raise ValueError('Cache non valida')
        poster=cache/(gif.stem+'.png')
        with POSTER_LOCK:
            if not poster.is_file() or poster.stat().st_mtime_ns<gif.stat().st_mtime_ns:
                temp=cache/(gif.stem+'.'+secrets.token_hex(4)+'.png')
                try:
                    result=subprocess.run([ffmpeg,'-nostdin','-hide_banner','-loglevel','error','-y','-i',str(gif),'-frames:v','1',str(temp)],capture_output=True,timeout=20)
                    if result.returncode or not temp.is_file():raise ValueError('Fotogramma non disponibile')
                    os.replace(temp,poster)
                finally:temp.unlink(missing_ok=True)
        send_file(handler,poster,'image/png')
    except (ValueError,OSError,subprocess.TimeoutExpired):handler.send_error(404)

def cleanup_plan(paths,scope,names=None):
    if scope not in ('previews','all','selected_previews'):raise ValueError('Ambito non valido')
    selected=None
    if scope=='selected_previews':
        if not isinstance(names,list) or not 1<=len(names)<=2000 or any(not isinstance(n,str) or not re.fullmatch(STEM+r'\.gif',n) for n in names):raise ValueError('Selezione anteprime non valida')
        selected={Path(n).stem for n in names}
    base,thumb=[Path(p).expanduser().resolve() for p in paths];files=[];counts=dict(videos=0,previews=0,auxiliary=0,bytes=0,files=0)
    sources=[(thumb,STEM+r'\.gif','previews'),(thumb,STEM+r'\.motion\.json','auxiliary'),(thumb/'.posters',STEM+r'\.png','auxiliary')]
    if scope=='all':sources.append((base,STEM+r'\.mp4','videos'))
    for directory,pattern,kind in sources:
        if directory.is_symlink() or not directory.is_dir():continue
        for f in directory.iterdir():
            if not re.fullmatch(pattern,f.name) or f.is_symlink() or not f.is_file():continue
            if selected is not None:
                stem=f.name[:-len('.motion.json')] if f.name.endswith('.motion.json') else f.stem
                if stem not in selected:continue
            stat=f.stat();files.append((str(f),stat.st_size,stat.st_mtime_ns));counts[kind]+=1;counts['bytes']+=stat.st_size;counts['files']+=1
    return dict(files=files,summary=counts)

def cleanup_execute(plan,trash_root=None):
    root=Path(trash_root) if trash_root is not None else Path.home()/'.Trash'
    root.mkdir(exist_ok=True,parents=True)
    destination=root/('V380-pulizia-'+secrets.token_hex(6));destination.mkdir()
    moved=0;errors=[]
    for name,size,mtime in plan['files']:
        f=Path(name)
        try:
            if f.is_symlink() or not f.is_file():continue
            stat=f.stat()
            if stat.st_size!=size or stat.st_mtime_ns!=mtime:raise ValueError('file cambiato dopo la conferma')
            dest=destination/f.name
            if dest.exists():dest=destination/(secrets.token_hex(4)+'_'+f.name)
            shutil.move(str(f),str(dest));moved+=1
        except (OSError,ValueError) as exc:errors.append(f.name+': '+str(exc))
    if moved==0:
        try:destination.rmdir()
        except OSError:pass
    return dict(moved=moved,errors=errors)
