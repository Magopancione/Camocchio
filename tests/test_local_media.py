"""Synthetic temporary fixtures only. No user files or camera accessed."""
import io,sys,tempfile,unittest,subprocess,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import local_media as m
class Handler:
 def __init__(self,value=None):self.headers={} if value is None else {'Range':value};self.wfile=io.BytesIO();self.response={}
 def send_response(self,status):self.status=status
 def send_error(self,status):self.status=status
 def send_header(self,k,v):self.response[k]=v
 def end_headers(self):pass
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.thumb=self.base/'Thumbnails';self.thumb.mkdir();self.stem='V380_2026-01-01_00-00-00';self.video=self.base/(self.stem+'.mp4');self.video.write_bytes(b'0123456789');self.gif=self.thumb/(self.stem+'.gif');self.gif.write_bytes(b'GIF89a');self.paths=(self.base,self.thumb)
 def tearDown(self):self.tmp.cleanup()
 def test_ranges(self):
  for value,status,data in [(None,200,b'0123456789'),('bytes=2-5',206,b'2345'),('bytes=-3',206,b'789'),('bytes=7-',206,b'789'),('bytes=99-',416,b''),('bytes=0-1,4-5',416,b''),('bytes=-0',416,b'')]:
   h=Handler(value);m.send_file(h,self.video,'video/mp4');self.assertEqual((h.status,h.wfile.getvalue()),(status,data))
 def test_paths(self):
  for name in ('../config.json','x.mp4',self.stem+'.mp4/..'):
   with self.assertRaises(ValueError):m.checked_file(self.base,name,'.mp4')
  h=Handler();m.serve_local(h,self.paths,'/media/local/video/'+self.video.name);self.assertEqual(h.status,200)
 def test_cleanup_preview_only(self):
  other=self.thumb/'keep.txt';other.write_text('keep');plan=m.cleanup_plan(self.paths,'previews');self.assertEqual(plan['summary']['videos'],0);self.assertEqual(plan['summary']['previews'],1)
  result=m.cleanup_execute(plan,self.base/'test-trash');self.assertEqual(result['moved'],1);self.assertTrue(self.video.exists());self.assertTrue(other.exists());self.assertFalse(self.gif.exists())
 def test_cleanup_all_changed_and_symlink(self):
  link=self.thumb/'V380_2026-01-02_00-00-00.gif';link.symlink_to(self.video);plan=m.cleanup_plan(self.paths,'all');self.assertEqual(plan['summary']['files'],2);self.video.write_bytes(b'changed');result=m.cleanup_execute(plan,self.base/'test-trash');self.assertEqual(result['moved'],1);self.assertEqual(len(result['errors']),1);self.assertTrue(self.video.exists());self.assertTrue(link.is_symlink())
 def test_poster(self):
  if not shutil.which('ffmpeg'):self.skipTest('ffmpeg absent')
  subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=blue:s=64x64:d=0.1','-frames:v','1',str(self.gif)],check=True)
  h=Handler();m.serve_poster(h,self.paths,'/media/poster/'+self.gif.name,'ffmpeg');self.assertEqual(h.status,200);self.assertTrue(h.wfile.getvalue().startswith(b'\x89PNG'))
if __name__=='__main__':unittest.main()
