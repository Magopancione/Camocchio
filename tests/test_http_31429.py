"""HTTP integration with temporary synthetic files. Never contacts a camera."""
import sys,tempfile,threading,json,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app
with tempfile.TemporaryDirectory() as td:
 root=Path(td);app.CFG=root/'config.json';app.LOG=root/'log.txt';app.pw=lambda:''
 base=root/'videos';base.mkdir();thumb=base/'Thumbnails';thumb.mkdir();stem='V380_2026-01-01_00-00-00';(base/(stem+'.mp4')).write_bytes(b'0123456789');(thumb/(stem+'.gif')).write_bytes(b'GIF89a')
 app.CFG.write_text(json.dumps({'save_dir':str(base)}))
 server=app.ThreadingHTTPServer(('127.0.0.1',0),app.H);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
 def post(path,data,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  req=urllib.request.Request(url+path,json.dumps(data).encode(),headers=headers)
  with urllib.request.urlopen(req) as r:return json.load(r)
 try:
  post('/api/settings',{'video_target':'internal','preview_target':'internal','gif_animation':'hover'})
  c=app.cfg();assert (c['video_target'],c['preview_target'],c['gif_animation'])==('internal','internal','hover')
  req=urllib.request.Request(url+'/media/local/video/'+stem+'.mp4',headers={'Range':'bytes=2-5'})
  with urllib.request.urlopen(req) as r:assert r.status==206 and r.read()==b'2345'
  plan=post('/api/cleanup-plan',{'scope':'all'});assert plan['files']==2 and (base/(stem+'.mp4')).exists()
  try:post('/api/cleanup-execute',{'token':'invalid'});raise AssertionError('bad token accepted')
  except urllib.error.HTTPError as e:assert e.code==400
  try:post('/api/cleanup-plan',{'scope':'all'},'https://example.invalid');raise AssertionError('cross origin accepted')
  except urllib.error.HTTPError as e:assert e.code==400
  assert (base/(stem+'.mp4')).exists() and (thumb/(stem+'.gif')).exists()
  print('PASS HTTP: preferences persisted, MP4 byte ranges, cleanup plan no mutation, invalid token and cross-origin rejected')
 finally:server.shutdown();server.server_close();thread.join()
