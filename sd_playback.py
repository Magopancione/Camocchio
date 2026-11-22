"""Experimental progressive microSD playback. No media written to disk."""
import os
import queue
import secrets
import socket
import struct
import subprocess
import threading
import time
from pathlib import Path


STEP_TABLE=(7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767)
INDEX_TABLE=(-1,-1,-1,-1,2,4,6,8)
def decode_ima_block(block):
    if len(block)!=256 or block[2]>88 or block[3]!=0:
        raise ValueError('Blocco IMA non compatibile')
    predictor=struct.unpack_from('<h',block)[0];index=block[2];samples=[predictor]
    for byte in block[4:]:
        for nibble in (byte&15,byte>>4):
            step=STEP_TABLE[index]
            # IMA WAV reference reconstruction: multiply before division.
            delta=((nibble&7)*2+1)*step//8
            predictor=max(-32768,min(32767,predictor+(-delta if nibble&8 else delta)))
            index=max(0,min(88,index+INDEX_TABLE[nibble&7]));samples.append(predictor)
    return struct.pack('<505h',*samples)

class Playback:
    def __init__(self, app):
        self.app = app
        self.lock = threading.RLock()
        self.session = None

    def status(self):
        with self.lock:
            s = self.session
            if not s:
                return {'running': False, 'message': 'Fermo', 'bytes': 0}
            return {k: s[k] for k in ('running', 'message', 'bytes')}

    def _finish(self, s, message):
        s['stop'].set()
        with self.lock:
            if s['released']:
                return
            s['released'] = True
            s['running'] = False
            s['message'] = message
            sock, proc = s.get('socket'), s.get('proc')
        if sock:
            try: sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            try: sock.close()
            except OSError: pass
        if proc and proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        self.app.JOB_LOCK.release()

    def stop(self):
        with self.lock: s = self.session
        if s and not s['released']:
            self._finish(s, 'Riproduzione fermata')

    def start(self, index, port, segment=None):
        # Do not silently interrupt an existing download or playback.
        if not self.app.JOB_LOCK.acquire(blocking=False):
            raise RuntimeError('Download o riproduzione SD gia in corso: fermare prima la sessione attiva')
        try:
            g = dict(segment) if segment is not None else dict(self.app.STATE['segments'][index])
            c = self.app.runtime()
            vlc = next((p for p in (Path('/Applications/VLC.app'), Path.home()/'Applications/VLC.app') if p.exists()), None)
            if vlc is None:
                raise RuntimeError('Installare VLC in Applicazioni per questo test')
            # Resolve dependency before opening player.
            self.app.ffmpeg()
            s = {'running': True, 'message': 'Attesa VLC...', 'bytes': 0,
                 'stop': threading.Event(), 'released': False, 'claimed': False,
                 'audio':bool(c.get('sd_stream_audio',False)), 'token': secrets.token_urlsafe(24), 'segment': g, 'config': c,
                 'socket': None, 'proc': None, 'started': time.monotonic()}
            with self.lock: self.session = s
            url = 'http://127.0.0.1:%d/sd-playback/%s.ts' % (port, s['token'])
            r = subprocess.run(['/usr/bin/open', '-a', str(vlc), url], capture_output=True)
            if r.returncode: raise RuntimeError('Impossibile aprire VLC')
        except Exception:
            if 's' in locals(): self._finish(s, 'Avvio fallito')
            else: self.app.JOB_LOCK.release()
            raise
        def timeout():
            # Maximum session 15 min, including player idle/backpressure.
            while not s['stop'].wait(1):
                elapsed = time.monotonic()-s['started']
                if (not s['claimed'] and elapsed > 30) or elapsed > 900:
                    self._finish(s, 'Timeout riproduzione SD'); return
        threading.Thread(target=timeout, daemon=True).start()

    def serve(self, handler, token):
        with self.lock:
            s = self.session
            if not s or not secrets.compare_digest(token, s['token']) or s['released']:
                handler.send_error(404); return
            if s['claimed']:
                handler.send_error(409); return
            s['claimed'] = True
        message = 'Riproduzione terminata'
        feed = None
        writers=[];audio_read=None;audio_write=None
        audio_queue=queue.Queue(maxsize=512);video_queue=queue.Queue(maxsize=64)
        response_sent = False
        try:
            c, g, app = s['config'], s['segment'], self.app
            ticket, _ = app.login(c)
            k = app.key(ticket)
            sock = socket.create_connection((c['host'], c['port']), 10)
            with self.lock:
                if s['stop'].is_set(): sock.close(); return
                s['socket'] = sock
            sock.settimeout(15)
            q = bytearray(64)
            for o,v in ((0,363),(4,c['device_id']),(8,ticket),(12,g['id'])):
                struct.pack_into('<I',q,o,v)
            app.clock(q,16,g['start']); q[23]=g['type']; sock.sendall(q)
            r = app.exact(sock,64)
            if struct.unpack_from('<I',r,0)[0]!=463 or struct.unpack_from('<i',r,4)[0]!=1000:
                raise RuntimeError('Playback microSD rifiutato')
            app.sendpb(sock,g,1)
            # Wait only for first decodable video payload, not the entire recording.
            pending=bytearray(); ack=lp=lf=0
            def packets():
                nonlocal ack,lp,lf
                while not s['stop'].is_set():
                    h=app.exact(sock,8);typ,note=h[0],h[1]
                    pkt,size=struct.unpack_from('<H',h,2)[0],struct.unpack_from('<H',h,4)[0]
                    pl=app.exact(sock,size) if size else b''
                    if typ==0xef:return
                    if typ==0x1f:continue
                    if typ==0x6f:app.sendpb(sock,g,2,note,lf,lp);ack=0;continue
                    if typ!=0x7f:raise RuntimeError('Pacchetto playback inatteso')
                    lp=pkt;ack+=1;pending.extend(pl)
                    while len(pending)>=22:
                        ft=struct.unpack_from('<H',pending,4)[0];fs=struct.unpack_from('<I',pending,18)[0]
                        if fs>16*1024*1024:raise RuntimeError('Frame playback troppo grande')
                        if len(pending)<22+fs:break
                        lf=struct.unpack_from('<I',pending,0)[0]
                        body=bytes(pending[22:22+fs]);del pending[:22+fs]
                        if ft==22 and s['audio']:
                            pcm=decode_ima_block(body)
                            while not s['stop'].is_set():
                                try:audio_queue.put(pcm,timeout=.25);break
                                except queue.Full:continue
                        if ft not in app.VIDEO:continue
                        data=app.payload(body,k)
                        if data:
                            s['bytes']+=len(data)
                            yield data
                    if ack>=200:app.sendpb(sock,g,2,note,lf,lp);ack=0
            stream=packets()
            first=next(stream,None)
            if not first:raise RuntimeError('Nessun video ricevuto dalla microSD')
            idx=3 if len(first)>3 and first[2]==1 else 4
            codec='h264' if first[idx]&31 in (1,5,7,8) else 'hevc'
            # Experimental fixed input rate: no verified source timestamps yet.
            cmd=[app.ffmpeg(),'-nostdin','-hide_banner','-loglevel','error',
                 '-probesize','32768','-analyzeduration','500000','-fflags','+genpts','-r','20','-f',codec,'-i','pipe:0',
                 '-an','-vf','scale=960:-2','-c:v','libx264','-preset','ultrafast',
                 '-tune','zerolatency','-pix_fmt','yuv420p','-threads','2',
                 '-g','40','-bf','0','-flush_packets','1','-f','mpegts','pipe:1']
            if s['audio']:
                audio_read,audio_write=os.pipe()
                insert=cmd.index('-an')
                cmd[insert:insert+1]=['-thread_queue_size','512','-f','s16le','-ar','8000','-ac','1','-i','pipe:'+str(audio_read),'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','16k','-ar','8000','-ac','1']
            try:
                proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,pass_fds=(audio_read,) if audio_read is not None else ())
            finally:
                if audio_read is not None:os.close(audio_read);audio_read=None
            with self.lock:
                if s['stop'].is_set(): proc.terminate();proc.wait();return
                s['proc']=proc
            s['message']='Riproduzione progressiva in VLC'+(' con audio sperimentale' if s['audio'] else ' (senza audio)')
            def enqueue(q,item):
                while not s['stop'].is_set():
                    try:q.put(item,timeout=.25);return
                    except queue.Full:continue
            def writer(q,pipe):
                try:
                    while not s['stop'].is_set():
                        try:data=q.get(timeout=.25)
                        except queue.Empty:continue
                        if data is None:break
                        pipe.write(data);pipe.flush()
                except (OSError,ValueError):
                    if not s['stop'].is_set():s['feed_error']=True
                finally:
                    try:pipe.close()
                    except OSError:pass
            vw=threading.Thread(target=writer,args=(video_queue,proc.stdin),daemon=True);vw.start();writers.append(vw)
            if s['audio']:
                ap=os.fdopen(audio_write,'wb',buffering=0);audio_write=None
                aw=threading.Thread(target=writer,args=(audio_queue,ap),daemon=True);aw.start();writers.append(aw)
            def write():
                try:
                    enqueue(video_queue,first)
                    for data in stream:
                        if s['stop'].is_set():break
                        enqueue(video_queue,data)
                except Exception:
                    if not s['stop'].is_set():s['feed_error']=True
                finally:
                    enqueue(video_queue,None)
                    if s['audio']:enqueue(audio_queue,None)
            feed=threading.Thread(target=write,daemon=True);feed.start()
            handler.send_response(200)
            response_sent = True
            handler.send_header('Content-Type','video/mp2t')
            handler.send_header('Cache-Control','no-store')
            handler.send_header('Connection','close');handler.end_headers();handler.close_connection=True
            while not s['stop'].is_set():
                data=proc.stdout.read1(65536)
                if not data:break
                handler.wfile.write(data);handler.wfile.flush()
            if s.get('feed_error'):message='Ricezione microSD interrotta; riprovare'
            elif proc.wait(timeout=5)!=0 and not s['stop'].is_set():message='Decodifica FFmpeg fallita; verificare supporto HEVC/H264 e libx264'
        except (BrokenPipeError,ConnectionResetError):message='Player disconnesso'
        except Exception as exc:
            # Do not expose configuration, tickets or keys.
            message='Errore playback SD: '+type(exc).__name__
        finally:
            if not response_sent:
                try:handler.send_error(503, 'Playback SD unavailable; see application status')
                except OSError:pass
            self._finish(s,message)
            if feed:feed.join(timeout=3)
            for writer_thread in writers:writer_thread.join(timeout=2)
            for fd in (audio_read,audio_write):
                if fd is not None:
                    try:os.close(fd)
                    except OSError:pass
