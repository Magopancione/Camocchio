"""RTSP -> local rolling HLS (H264/AAC). Separate from stable SD playback."""
import http.client
import json
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import quote


def rtsp_url(config, password=''):
    host=str(config.get('host','')).strip()
    port=int(config.get('rtsp_port',554));path=str(config.get('rtsp_path','/11'))
    if not host or any(c in host for c in '/@?# \r\n') or not 1<=port<=65535:
        raise ValueError('Host o porta RTSP non validi')
    if not path.startswith('/') or any(c in path for c in '?@#\r\n'):
        raise ValueError('Percorso RTSP non valido')
    transport=config.get('rtsp_transport','tcp')
    if transport not in ('tcp','udp'):raise ValueError('Trasporto RTSP non valido')
    auth=''
    if config.get('rtsp_auth',False):
        if not password:raise ValueError('Password RTSP assente nel Portachiavi')
        auth=quote(str(config.get('username','')),safe='')+':'+quote(password,safe='')+'@'
    return 'rtsp://'+auth+host+':'+str(port)+path


def hls_command(ffmpeg, input_args, directory, separate_audio=False):
    return [ffmpeg,'-nostdin','-hide_banner','-loglevel','info',*input_args,
            '-map','0:v:0','-map',('1:a:0' if separate_audio else '0:a:0?'),'-vf','fps=20,scale=960:-2',
            '-c:v','libx264','-preset','ultrafast','-tune','zerolatency',
            '-pix_fmt','yuv420p','-threads','2','-g','40','-keyint_min','40',
            '-sc_threshold','0','-bf','0','-c:a','aac','-b:a','48k','-ac','1','-ar','24000',
            '-f','hls','-hls_time','2','-hls_list_size','5','-hls_delete_threshold','2',
            '-hls_flags','delete_segments+temp_file+independent_segments',
            '-hls_segment_filename',str(directory/'segment_%08d.ts'),str(directory/'live.m3u8')]


def source_args(config,password):
    url=rtsp_url(config,password)
    transport=config.get('rtsp_transport','tcp')
    args=['-rtsp_transport',transport,'-i',url]
    path=str(config.get('rtsp_audio_path','')).strip()
    if path and path!=str(config.get('rtsp_path','/11')):
        alternate=rtsp_url(dict(config,rtsp_path=path),password)
        return args+['-rtsp_transport',transport,'-allowed_media_types','audio','-i',alternate],True
    return args,False


def inspect_source(ffprobe,config,password):
    args,separate=source_args(config,password)
    urls=[args[3]]+([args[-1]] if separate else [])
    results=[]
    for i,url in enumerate(urls):
        try:
            result=subprocess.run([ffprobe,'-v','error','-rtsp_transport',config.get('rtsp_transport','tcp'),'-show_entries','stream=codec_name,codec_type','-of','json',url],capture_output=True,timeout=9)
            if result.returncode:raise ValueError('probe failed')
            streams=json.loads(result.stdout).get('streams',[])
            def codecs(kind):
                return [v for stream in streams if stream.get('codec_type')==kind for v in [stream.get('codec_name','')] if re.fullmatch(r'[a-zA-Z0-9_]{1,40}',v)]
            results.append({'source':i,'video':codecs('video'),'audio':codecs('audio'),'ok':True})
        except (OSError,ValueError,subprocess.TimeoutExpired):
            results.append({'source':i,'ok':False})
    return results


def local_relay_args(url):
    # Explicit local adapter only: no discovery, credentials, remote URLs or redirects.
    m=re.fullmatch(r'http://127\.0\.0\.1:([0-9]{1,5})/live\.flv',url) if isinstance(url,str) else None
    if not m or not 1<=int(m[1])<=65535:
        raise ValueError('Usare http://127.0.0.1:PORTA/live.flv del bridge locale')
    return int(m[1])


class LiveAV:
    def __init__(self, app):
        self.app=app;self.lock=threading.RLock();self.control=threading.RLock();self.session=None

    def start(self, relay=None):
        with self.control:self._start(relay)

    def _start(self, relay=None):
        port=local_relay_args(relay) if relay is not None else None
        self.stop()
        config=self.app.cfg();password=self.app.pw() if port is None and config.get('rtsp_auth',False) else ''
        args,separate=source_args(config,password) if port is None else (['-f','flv','-i','pipe:0'],False)
        directory=Path(tempfile.mkdtemp(prefix='v380_live_'))
        try:
            proc=subprocess.Popen(hls_command(self.app.ffmpeg(),args,directory,*([True] if separate else [])),
                                  stdin=subprocess.PIPE if port is not None else subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        except Exception:
            shutil.rmtree(directory,ignore_errors=True);raise
        s=dict(proc=proc,directory=directory,token=secrets.token_urlsafe(24),audio=False,error='',warning='',
               stop=threading.Event(),started=time.monotonic())
        with self.lock:self.session=s
        if port is not None:
            def feed():
                conn=http.client.HTTPConnection('127.0.0.1',port,timeout=8)
                try:
                    conn.request('GET','/live.flv',headers={'Accept-Encoding':'identity'})
                    with conn.getresponse() as response:
                        if response.status!=200 or response.read(3)!=b'FLV':
                            raise ValueError('Not FLV')
                        proc.stdin.write(b'FLV')
                        while not s['stop'].is_set():
                            block=response.read1(16384)
                            if not block:break
                            proc.stdin.write(block);proc.stdin.flush()
                except (OSError,ValueError,http.client.HTTPException):
                    if not s['stop'].is_set():s['error']='Bridge locale non disponibile o risposta non FLV'
                finally:
                    conn.close()
                    try:proc.stdin.close()
                    except OSError:pass
            threading.Thread(target=feed,daemon=True).start()
        def diagnostic():
            try:
                output=False
                for raw in iter(proc.stderr.readline,b''):
                    line=raw.decode(errors='replace')
                    if line.startswith('Output #0, hls,'):output=True
                    if output and re.match(r'\s*Stream #0:.*Audio:',line):s['audio']=True
                    if any(word in line.lower() for word in ('error','failed','invalid','denied','not found','refused','timed out')):
                        # URLs and credentials never leave the process diagnostic boundary.
                        line=re.sub(r'rtsp://\S+','[RTSP]',line)
                        for secret in (password,quote(password,safe='') if password else '',str(config.get('host','')),str(config.get('username',''))):
                            if secret:line=line.replace(secret,'[redacted]')
                        if 'Skipping invalid undecodable NALU' in line or 'Error constructing the frame RPS' in line:
                            s['warning']=line.strip()[:400]
                        elif not s['error']:s['error']=line.strip()[:400]
            finally:proc.stderr.close()
        threading.Thread(target=diagnostic,daemon=True).start()
        def watchdog():
            while not s['stop'].wait(1):
                if proc.poll() is not None:
                    if not s['error']:s['error']='Flusso Live terminato'
                    return
                playlist=directory/'live.m3u8'
                if playlist.exists():
                    try:stalled=time.time()-playlist.stat().st_mtime>25
                    except FileNotFoundError:return
                else:stalled=time.monotonic()-s['started']>35
                try:cache_bytes=sum(f.stat().st_size for f in directory.glob('*.ts'))
                except FileNotFoundError:continue
                if cache_bytes>64*1024*1024:
                    s['error']='Buffer Live oltre 64 MB';proc.terminate();return
                if stalled:
                    s['error']='Timeout Live audio/video: verificare sorgente, rete e permessi';proc.terminate();return
        threading.Thread(target=watchdog,daemon=True).start()

    def status(self):
        with self.lock:
            s=self.session
            if not s:return dict(running=False,ready=False,audio=False,error='',warning='',url=None)
            ready=(s['directory']/'live.m3u8').is_file()
            return dict(running=s['proc'].poll() is None,ready=ready,audio=s['audio'],error=s['error'],warning=s.get('warning',''),
                        url='/live-av/'+s['token']+'/live.m3u8' if ready else None)

    def stop(self):
        with self.control:self._stop()

    def _stop(self):
        with self.lock:s=self.session;self.session=None
        if not s:return
        s['stop'].set();proc=s['proc']
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=4)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        shutil.rmtree(s['directory'],ignore_errors=True)

    def serve(self, handler, path):
        parts=path.split('/')
        if len(parts)!=4:handler.send_error(404);return
        token,name=parts[2:]
        if not (name=='live.m3u8' or re.fullmatch(r'segment_\d{8}\.ts',name)):
            handler.send_error(404);return
        with self.lock:
            s=self.session
            if not s or not secrets.compare_digest(token,s['token']):handler.send_error(404);return
            try:data=(s['directory']/name).read_bytes()
            except FileNotFoundError:handler.send_error(404);return
        handler.send_response(200)
        handler.send_header('Content-Type','application/vnd.apple.mpegurl' if name.endswith('.m3u8') else 'video/mp2t')
        handler.send_header('Cache-Control','no-store');handler.send_header('Content-Length',str(len(data)));handler.end_headers()
        try:handler.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
