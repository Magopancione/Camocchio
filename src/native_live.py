"""Authenticated local viewing for the Camocchio firmware tested on TCP 8800."""
import ipaddress
import queue
import re
import socket
import struct
import threading
import time

from sd_playback import decode_ima_block

LAN = tuple(ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16','169.254.0.0/16'))
VIDEO = {0, 1, 0x28, 0x29, 0x32, 0x33, 0x34, 0x35}
BOUND = 2 * 1024 * 1024
START = re.compile(rb'\x00\x00(?:\x00)?\x01')


def configuration(app):
    cfg = app.cfg()
    try:
        address = ipaddress.IPv4Address(cfg.get('host',''))
        if cfg.get('port') != 8800 or not any(address in net for net in LAN):
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('Live 8800: configura un IPv4 locale e la porta TCP 8800') from None
    c = app.runtime()
    c.update(host=str(address), port=8800)
    if not 1 <= c['device_id'] <= 0xffffffff or not 1 <= len(c['username'].encode()) <= 32 or not 1 <= len(c['password'].encode()) <= 31:
        raise ValueError('Live 8800: identificativo o credenziali non compatibili')
    return c


def exact(sock, size, seconds=4):
    end = time.monotonic() + seconds
    b = bytearray()
    while len(b) < size:
        left = end - time.monotonic()
        if left <= 0:
            raise socket.timeout()
        sock.settimeout(left)
        part = sock.recv(size - len(b))
        if not part:
            raise EOFError()
        b.extend(part)
    return bytes(b)


def setup(sock, device, ticket, quality=0):
    # Same 301/303 exchange as the 3.14.39 diagnostic, with the selected profile.
    request = bytearray(256)
    struct.pack_into('<II',request,0,301,device)
    struct.pack_into('<H',request,12,20)
    struct.pack_into('<I',request,14,ticket)
    struct.pack_into('<II',request,22,4097,quality)
    sock.settimeout(4)
    sock.sendall(request)
    reply = bytearray(exact(sock,18))
    end = time.monotonic() + .25
    while len(reply) < 412 and time.monotonic() < end:
        sock.settimeout(max(.001,end-time.monotonic()))
        try: part = sock.recv(412-len(reply))
        except socket.timeout: break
        if not part: break
        reply.extend(part)
    command, code = struct.unpack_from('<Ii',reply)
    if command != 401 or code not in (402,1001,-11,-12):
        raise ValueError('Live 8800: richiesta di diretta rifiutata')
    start = reply.ljust(412,b'\0')
    struct.pack_into('<Ii',start,0,303,code)
    sock.settimeout(4)
    sock.sendall(start)


def frames(sock, stop):
    pending = {}
    while not stop.is_set():
        header = exact(sock,12)
        if header[0] in (0x1f, 0x6f):
            continue
        if header[0] != 0x7f:
            raise ValueError('Live 8800: intestazione media non riconosciuta')
        kind = header[1]
        count, index, size = struct.unpack_from('<HHH',header,3)
        if not 0 <= index < count <= 8192 or not 1 <= size <= 8192:
            raise ValueError('Live 8800: frammento non compatibile')
        body = exact(sock,size)
        if kind not in VIDEO and kind != 0x16:
            continue
        if index == 0:
            pending[kind] = (count,0,bytearray())
        state = pending.get(kind)
        if not state or state[:2] != (count,index) or len(state[2])+size > BOUND:
            raise ValueError('Live 8800: sequenza di frammenti incompleta')
        state[2].extend(body)
        if index+1 == count:
            del pending[kind]
            yield kind,bytes(state[2])
        else:
            pending[kind] = (count,index+1,state[2])


def hevc(app, data, key):
    mark = START.search(data[:36])
    if not mark:
        data = app.decvid(data,key)
        mark = START.search(data[:36])
    if not mark or mark.end()+2 > len(data):
        return b'', ()
    data = data[mark.start():]
    units = tuple((data[m.end()]>>1)&63 for m in START.finditer(data) if m.end()+2<=len(data))
    return data,units


class NativeFeed:
    def __init__(self, quality=0):
        self.quality = quality
        self.stop_event = threading.Event()
        self.guard = threading.Lock()
        self.sock = None
        self.audio_blocks = 0
        self.video_units = 0
        self.fps = None
        self.queues = (queue.Queue(64),queue.Queue(128))

    def stop(self):
        self.stop_event.set()
        with self.guard:
            if self.sock:
                try:self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:pass

    def enqueue(self, index, body):
        if self.stop_event.is_set(): raise InterruptedError()
        try:self.queues[index].put(body,timeout=2)
        except queue.Full:raise RuntimeError('Live 8800: conversione troppo lenta, riavvia la diretta') from None

    def pump(self, index, pipe, fail):
        try:
            while not self.stop_event.is_set():
                try:body = self.queues[index].get(timeout=.2)
                except queue.Empty:continue
                pipe.write(body)
                pipe.flush()
        except (OSError,ValueError):
            if not self.stop_event.is_set():fail('Live 8800: FFmpeg non riceve più il flusso')
        finally:
            try:pipe.close()
            except OSError:pass

    def run(self, app, start_encoder):
        c = configuration(app)
        ticket,_ = app.login(c)
        if not ticket:raise ValueError('Live 8800: accesso non confermato')
        if self.stop_event.is_set():return
        key = app.key(ticket)
        with socket.create_connection((c['host'],8800),timeout=4) as sock:
            with self.guard:
                if self.stop_event.is_set():return
                self.sock = sock
            try:
                setup(sock,c['device_id'],ticket,self.quality)
                self._feed(app,key,frames(sock,self.stop_event),start_encoder)
            finally:
                with self.guard:self.sock = None

    def _feed(self, app, key, stream, start_encoder):
        # Begin at an HEVC random-access picture; discard earlier audio while aligning.
        prefix = bytearray(); saved = []; size = 0; start = None
        deadline = time.monotonic()+14
        for kind,data in stream:
            now = time.monotonic()
            if self.fps is None and now>deadline:
                raise RuntimeError('Live 8800: attesa del fotogramma iniziale o dell’audio scaduta')
            picture = False
            if kind == 0x16:
                if start is None:continue
                if len(data)!=272:raise ValueError('Live 8800: blocco audio non compatibile')
                try:body = decode_ima_block(data[16:])
                except ValueError:raise ValueError('Live 8800: blocco audio IMA non compatibile') from None
                index = 1; self.audio_blocks += 1
            else:
                body,units = hevc(app,data,key)
                if not body:continue
                picture = any(n<32 for n in units)
                if start is None:
                    if not any(16<=n<=23 for n in units):
                        if not picture and any(n in (32,33,34) for n in units):
                            prefix.extend(body)
                            if len(prefix)>65536:prefix.clear()
                        continue
                    start=now; body=bytes(prefix)+body
                index=0
                self.video_units += picture
            if self.fps is not None:
                self.enqueue(index,body)
                continue
            saved.append((index,body));size+=len(body)
            if size>8*1024*1024 or len(saved)>360:
                raise RuntimeError('Live 8800: buffer iniziale esaurito, audio o video assente')
            # Count pictures against the independently measured sample clock.
            if self.audio_blocks>=48 and self.video_units>=8 and now-start>=2.6:
                rate=self.video_units*8000/(self.audio_blocks*505)
                nearest=min((8,10,12,12.5,15,20,24,25,30,50,60),key=lambda f:abs(f-rate))
                if not 3<=rate<=65:raise ValueError('Live 8800: cadenza video iniziale non plausibile')
                self.fps=nearest if abs(nearest-rate)/nearest<.045 else round(rate,3)
                start_encoder(self.fps)
                for n,payload in saved:self.enqueue(n,payload)
                saved.clear()
        if not self.stop_event.is_set():raise EOFError()


def encoder_inputs(audio_fd, fps):
    return ['-thread_queue_size','96','-probesize','32768','-analyzeduration','300000',
            '-r',str(fps),'-f','hevc','-i','pipe:0',
            '-thread_queue_size','128','-f','s16le','-ar','8000','-ac','1','-i','pipe:'+str(audio_fd)]
