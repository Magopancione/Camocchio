"""RTSP -> local rolling HLS (H264/AAC). Separate from stable SD playback."""
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import quote
from native_live import NativeFeed, encoder_inputs


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


def hls_command(ffmpeg, input_args, directory, separate_audio=False, *, native_quality=None):
    vf="fps=20,scale=960:-2" if native_quality!="high" else "fps=20,scale=w=min(iw\\,1920):h=-2"
    window="22" if native_quality else "5"
    return [ffmpeg,'-nostdin','-hide_banner','-loglevel','info',*input_args,
            '-map','0:v:0','-map',('1:a:0' if separate_audio else '0:a:0?'),'-vf',vf,
            '-c:v','libx264','-preset','ultrafast','-tune','zerolatency',
            '-pix_fmt','yuv420p','-threads','2','-g','40','-keyint_min','40',
            '-sc_threshold','0','-bf','0','-c:a','aac','-b:a','48k','-ac','1','-ar','24000',
            '-f','hls','-hls_time','2','-hls_list_size',window,'-hls_delete_threshold','2',
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


class LiveAV:
    def __init__(self, app):
        self.app=app;self.lock=threading.RLock();self.control=threading.RLock();self.session=None

    def start(self):
        with self.control:self._start()

    def start_native(self, quality="low"):
        if quality not in ("low", "high"):
            raise ValueError("Qualità Live non valida")
        with self.control:
            self._stop()
            if not self.app.JOB_LOCK.acquire(blocking=False):
                raise RuntimeError('Ferma la riproduzione microSD o attendi il download prima del Live 8800')
            directory=None
            try:
                exe=self.app.ffmpeg()
                directory=Path(tempfile.mkdtemp(prefix='camocchio_live8800_'))
                feed=NativeFeed(int(quality=="high"))
                s=dict(native=feed,proc=None,directory=directory,token=secrets.token_urlsafe(24),audio=True,
                       error='',warning='',done=False,started=time.monotonic(),quality=quality,first_playlist_ms=None)
                s['worker']=threading.Thread(target=self._native_worker,args=(s,exe),daemon=True)
                with self.lock:self.session=s
                s['worker'].start()
            except BaseException:
                with self.lock:self.session=None
                if directory:shutil.rmtree(directory,ignore_errors=True)
                self.app.JOB_LOCK.release()
                raise

    @staticmethod
    def _terminate(proc):
        if proc and proc.poll() is None:
            try:
                proc.terminate();proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=3)
            except ProcessLookupError:pass

    def _native_worker(self,s,exe):
        feed=s['native']; writers=[]; watchdog=None
        def fail(message):
            with self.lock:
                if not feed.stop_event.is_set() and not s['error']:s['error']=message
            feed.stop()
        def start_encoder(fps):
            nonlocal watchdog
            read,write=os.pipe()
            try:
                with self.lock:
                    if feed.stop_event.is_set():raise InterruptedError()
                    s['proc']=proc=subprocess.Popen(hls_command(exe,encoder_inputs(read,fps),s['directory'],True, native_quality=s['quality']),
                            stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,pass_fds=(read,))
                with os.fdopen(write,'wb',buffering=0,closefd=False) as audio:
                    # Transfer ownership to the writer using a duplicate, leaving original cleanup here.
                    pipe=os.fdopen(os.dup(audio.fileno()),'wb')
                for index,stream in enumerate((proc.stdin,pipe)):
                    t=threading.Thread(target=feed.pump,args=(index,stream,fail),daemon=True)
                    t.start();writers.append(t)
            finally:
                os.close(read);os.close(write)
            def monitor():
                latest=time.monotonic()
                previous=None
                playlist=s['directory']/'live.m3u8'
                while not feed.stop_event.wait(.5):
                    if proc.poll() is not None:
                        fail('Live 8800: conversione FFmpeg terminata');return
                    try:
                        modified=playlist.stat().st_mtime_ns
                        if modified!=previous:latest=time.monotonic();previous=modified
                        if s['first_playlist_ms'] is None:s['first_playlist_ms']=round((latest-s['started'])*1000)
                    except OSError:pass
                    try:over=sum(p.stat().st_size for p in s['directory'].glob('*.ts*'))>64*1024*1024
                    except OSError:over=False
                    if over or time.monotonic()-latest>18:
                        fail('Live 8800: limite buffer o timeout del player');return
            watchdog=threading.Thread(target=monitor,daemon=True);watchdog.start()
        try:feed.run(self.app,start_encoder)
        except Exception as exc:
            message=str(exc)
            if not message.startswith('Live 8800:'):
                message='Live 8800: connessione interrotta o audio/video non disponibile'
            if not feed.stop_event.is_set():fail(message)
        finally:
            feed.stop()
            try:
                self._terminate(s['proc'])
                for writer in writers:writer.join(timeout=1)
                if watchdog:watchdog.join(timeout=1)
            finally:
                shutil.rmtree(s['directory'],ignore_errors=True)
                self.app.JOB_LOCK.release()
                with self.lock:s['done']=True

    def _start(self):
        self.stop()
        config=self.app.cfg();password=self.app.pw() if config.get('rtsp_auth',False) else ''
        args,separate=source_args(config,password)
        directory=Path(tempfile.mkdtemp(prefix='v380_live_'))
        try:
            proc=subprocess.Popen(hls_command(self.app.ffmpeg(),args,directory,*([True] if separate else [])),
                                  stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        except Exception:
            shutil.rmtree(directory,ignore_errors=True);raise
        s=dict(proc=proc,directory=directory,token=secrets.token_urlsafe(24),audio=False,error='',warning='',
               stop=threading.Event(),started=time.monotonic())
        with self.lock:self.session=s
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
            if 'native' in s:
                feed=s['native'];ready=(s['directory']/'live.m3u8').is_file() and not feed.stop_event.is_set()
                return dict(running=not s['done'],ready=ready,audio=ready and feed.audio_blocks>0,error=s['error'],
                            url='/live-av/'+s['token']+'/live.m3u8' if ready else None,
                            source='tcp8800',fps_estimated=feed.fps,audio_blocks=feed.audio_blocks,
                            video_pictures=feed.video_units,quality=s['quality'],first_playlist_ms=s['first_playlist_ms'])
            ready=(s['directory']/'live.m3u8').is_file()
            return dict(running=s['proc'].poll() is None,ready=ready,audio=s['audio'],error=s['error'],warning=s.get('warning',''),
                        url='/live-av/'+s['token']+'/live.m3u8' if ready else None)

    def stop(self):
        with self.control:self._stop()

    def _stop(self):
        with self.lock:s=self.session;self.session=None
        if not s:return
        if 'native' in s:
            s['native'].stop();s['worker'].join(timeout=3);return
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
