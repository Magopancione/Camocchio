from pathlib import Path
import sys,tempfile,subprocess,json,time
from unittest.mock import patch
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'));import app
from datetime import datetime
stamp=datetime(2026,1,2,12,30,0).timestamp();g=dict(id=42,start=stamp,end=stamp+120,display_start=stamp,display_end=stamp+120)
original_segments=[dict(id=99)]
app.STATE['segments']=original_segments
with patch.object(app,'runtime',return_value={}),patch.object(app,'login',return_value=(1,1)),patch.object(app,'listrec',return_value=[g]):
 assert app.resolve_gallery_segment('V380_2026-01-02_12-30-00')['id']==42
 assert app.STATE['segments'] is original_segments
with patch.object(app,'runtime',return_value={}),patch.object(app,'login',return_value=(1,1)),patch.object(app,'listrec',return_value=[]):
 try:app.resolve_gallery_segment('V380_2026-01-02_12-30-00');raise AssertionError()
 except RuntimeError as e:assert 'non trovata' in str(e)
print('PASS: resolve exact SD recording from GIF stem without altering current day; missing recording rejected')
saved=[]
with patch.object(app,'runtime',return_value={}),patch.object(app,'local_media_state',return_value=(None,None)),patch.object(app,'save_recording',side_effect=lambda c,x:saved.append(x['id'])):
 app.begin_download([],segments_override=[g]);deadline=time.time()+3
 while app.STATE['busy'] and time.time()<deadline:time.sleep(.01)
 assert saved==[42] and app.STATE['segments'] is original_segments
print('PASS: gallery download uses exact snapshot, leaves selected day untouched')
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'sample.gif'
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=64x64:rate=2:duration=1','-threads','1','-y',str(p)],check=True)
 p.with_suffix('.motion.json').write_text(json.dumps({'mode':'motion','sensitivity':'medium','interval':[1,120]}))
 info=app.preview_details(p);assert info['bytes']==p.stat().st_size and info['report']['mode']=='motion';assert info['probe']['streams'][0]['width']==64
print('PASS: real GIF file size, method metadata, resolution and frame count probed')
