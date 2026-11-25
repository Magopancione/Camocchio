"""Temporary synthetic files and mocked AppKit only. No user media/camera accessed."""
import sys,tempfile,unittest,threading,json,urllib.request,urllib.error,types
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app,local_media,desktop
class Changes(unittest.TestCase):
 def test_selected_previews(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);thumb=root/'Thumbnails';thumb.mkdir();posters=thumb/'.posters';posters.mkdir()
   stems=['V380_2026-01-01_00-00-00','V380_2026-01-01_00-02-00']
   for stem in stems:
    (root/(stem+'.mp4')).write_bytes(b'video');(thumb/(stem+'.gif')).write_bytes(b'gif');(thumb/(stem+'.motion.json')).write_text('{}');(posters/(stem+'.png')).write_bytes(b'png')
   plan=local_media.cleanup_plan((root,thumb),'selected_previews',[stems[1]+'.gif'])
   self.assertEqual(plan['summary']['previews'],1);self.assertEqual(plan['summary']['videos'],0);self.assertEqual(plan['summary']['auxiliary'],2)
   result=local_media.cleanup_execute(plan,root/'trash');self.assertEqual(result['moved'],3)
   self.assertTrue((thumb/(stems[0]+'.gif')).exists());self.assertFalse((thumb/(stems[1]+'.gif')).exists())
   self.assertTrue(all((root/(stem+'.mp4')).exists() for stem in stems))
   for names in ([],['../x.gif'],[stems[0]+'.mp4'],[None]):
    with self.assertRaises(ValueError):local_media.cleanup_plan((root,thumb),'selected_previews',names)
 def test_http_identity_and_external_choices(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);thumb=root/'Thumbnails';thumb.mkdir();stem='V380_2026-01-01_00-00-00';(root/(stem+'.mp4')).write_bytes(b'video');(thumb/(stem+'.gif')).write_bytes(b'gif')
   config=root/'config.json';config.write_text(json.dumps({'save_dir':str(root),'device_id':123,'username':'123'}))
   with patch.object(app,'CFG',config),patch.object(app,'LOG',root/'log'),patch.object(app,'pw',return_value=''):
    server=app.ThreadingHTTPServer(('127.0.0.1',0),app.H);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    def post(path,data):
     req=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+path,json.dumps(data).encode(),headers={'Content-Type':'application/json'})
     with urllib.request.urlopen(req) as r:return json.load(r)
    try:
     post('/api/settings',{'device_id':456,'username':'ignored','player':'IINA','preview_player':'Preview'})
     self.assertEqual(app.cfg()['username'],'456');self.assertEqual(app.cfg()['device_id'],456)
     with patch.object(app.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
      post('/api/open',{'kind':'video','name':stem+'.mp4'});self.assertEqual(run.call_args.args[0][2],'IINA')
      post('/api/open',{'kind':'thumb','name':stem+'.gif'});self.assertEqual(run.call_args.args[0][2],'Preview')
     with patch.object(app.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)):
      with self.assertRaises(urllib.error.HTTPError):post('/api/open',{'kind':'video','name':stem+'.mp4'})
     for data in ({'device_id':-1},{'device_id':0},{'device_id':4294967296},{'player':'unknown'}):
      with self.assertRaises(urllib.error.HTTPError):post('/api/settings',data)
     plan=post('/api/cleanup-plan',{'scope':'selected_previews','names':[stem+'.gif']});self.assertEqual(plan['previews'],1);self.assertEqual(plan['videos'],0)
     self.assertTrue((root/(stem+'.mp4')).exists());self.assertTrue((thumb/(stem+'.gif')).exists())
    finally:server.shutdown();server.server_close();t.join()
 def test_native_titlebar_contract(self):
  class Button:
   def setHidden_(self,value):self.hidden=value
  class Native:
   def __init__(self):self.mask=15;self.buttons={i:Button() for i in range(3)}
   def styleMask(self):return self.mask
   def setStyleMask_(self,value):self.mask=value
   def setTitlebarAppearsTransparent_(self,value):self.transparent=value
   def setTitleVisibility_(self,value):self.title=value
   def setBackgroundColor_(self,value):self.color=value
   def standardWindowButton_(self,kind):return self.buttons[kind]
   def setMovableByWindowBackground_(self,value):self.move=value
   def contentView(self):return None
  kit=types.ModuleType('AppKit');kit.NSColor=types.SimpleNamespace(colorWithSRGBRed_green_blue_alpha_=lambda *a:a)
  for key,value in [('NSFullSizeContentViewWindowMask',1<<15),('NSWindowTitleHidden',1),('NSWindowCloseButton',0),('NSWindowMiniaturizeButton',1),('NSWindowZoomButton',2)]:setattr(kit,key,value)
  foundation=types.ModuleType('Foundation');foundation.NSThread=types.SimpleNamespace(isMainThread=lambda:False)
  tools=types.ModuleType('PyObjCTools');calls=[]
  def call_after(fn):calls.append('main-thread-dispatch');fn()
  tools.AppHelper=types.SimpleNamespace(callAfter=call_after)
  api=desktop.AppearanceAPI();native=Native();api._window=types.SimpleNamespace(native=native)
  with patch.dict(sys.modules,{'AppKit':kit,'Foundation':foundation,'PyObjCTools':tools}),patch.object(app,'log'):
   self.assertFalse(api.set_titlebar_color('bad')['ok'])
   self.assertTrue(api.set_titlebar_color('#06230d')['ok']);self.assertTrue(native.mask&(1<<15));self.assertTrue(native.transparent)
   self.assertTrue(all(not b.hidden for b in native.buttons.values()));self.assertEqual(calls,['main-thread-dispatch'])
   api._window.native=None;self.assertFalse(api.set_titlebar_color('#06230d')['ok'])
if __name__=='__main__':unittest.main()
