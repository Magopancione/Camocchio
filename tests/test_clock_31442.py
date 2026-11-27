"""Exercise the saved preference through HTTP and the real list parser."""
from datetime import datetime
import io,json,struct,sys,tempfile,threading,urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app

start=int(datetime(2026,11,26,8,1,56).timestamp());end=start+120
reply=bytearray(512);struct.pack_into('<IHHIBII',reply,0,462,1,1,11,3,start,end)
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);cfg=root/'config.json'
    cfg.write_text(json.dumps({'host':'fixture.invalid','device_id':123,'username':'123','save_dir':folder}))
    class Camera:
        def __enter__(self):self.body=io.BytesIO(struct.pack('<Ii',461,1).ljust(32,b'\0')+reply+bytes(512));return self
        def __exit__(self,*args):pass
        def settimeout(self,*args):pass
        def sendall(self,*args):pass
        def recv(self,n):return self.body.read(n)
    with patch.object(app,'CFG',cfg),patch.object(app,'pw',return_value='dummy'),patch.object(app,'login',return_value=(1,3)),patch.object(app,'log'):
        server=app.ThreadingHTTPServer(('127.0.0.1',0),app.H);t=threading.Thread(target=server.serve_forever);t.start()
        original=app.socket.create_connection
        def dial(address,*args,**kw):return Camera() if address[0]=='fixture.invalid' else original(address,*args,**kw)
        def post(path,data):
            req=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+path,json.dumps(data).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=4) as f:return json.load(f)
        try:
            with patch.object(app.socket,'create_connection',side_effect=dial):
                for enabled,expected in [(False,('08:01:56','08:03:56')),(True,('07:01:56','07:03:56')),(False,('08:01:56','08:03:56'))]:
                    post('/api/settings',{'time_correction':enabled});item=post('/api/list',{'day':'2026-11-26'})['items'][0]
                    assert (item['start'],item['end'])==expected,item
                    raw=app.STATE['segments'][0];assert (raw['start'],raw['end'])==(start,end)
        finally:server.shutdown();server.server_close();t.join()
print('PASS: saved clock preference reaches SD list parser, reversible without modifying raw timestamps')
