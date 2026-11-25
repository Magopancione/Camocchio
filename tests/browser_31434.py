import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app
calls=[];stops=[];errors=[]
stem='V380_2026-11-24_12-00-00'
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,**({'executable_path':os.environ['BROWSER_PATH']} if os.environ.get('BROWSER_PATH') else {}))
 page=browser.new_page(viewport={'width':1200,'height':680});page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  path=r.request.url.split('http://test.local')[-1].split('?')[0]
  if path=='/':return r.fulfill(body=app.HTML,content_type='text/html')
  data={'ok':1}
  if path=='/api/config':data={'has_password':True,'host':'camera.test','device_id':123,'sd_target':'internal','preview_mode':'uniform'}
  if path=='/api/list':data={'items':[{'start':'12:00:00','end':'12:02:00','downloaded':False,'preview':i==0,'local_stem':stem if i==0 else None} for i in range(40)]}
  if path=='/api/library':data={'items':[{'name':stem,'thumb':'a.gif','video':None,'preview_kind':'motion','date':'24-11-2026'}]}
  if path=='/api/preview-info':data={'preview':{'filename':'a.gif','bytes':1000,'path':'/test/a.gif','modified':'2026-11-24T12:00:00','report':{'mode':'motion','events':[[1,2],[4,5],[10,11]]}}}
  if path in ('/api/sd-playback-start','/api/gallery-sd'):calls.append(r.request.post_data_json);data={'target':'internal'}
  if path=='/api/sd-playback-stop':stops.append(True)
  if path=='/api/sd-playback-status':data={'running':False,'message':'Pronto','playlist':'/sd-hls/sample/index.m3u8'} if len(calls)>len(stops) else {'running':False,'message':'Fermo'}
  if path.startswith(('/media/','/assets/','/sd-hls/')):return r.fulfill(status=404)
  r.fulfill(body=json.dumps(data),content_type='application/json')
 page.route('http://test.local/**',route);page.goto('http://test.local/');page.wait_for_selector('.recordingCard')
 sidebar=page.locator('.shell>aside');main=page.locator('.shell>main');y=sidebar.bounding_box()['y'];main.evaluate('e=>e.scrollTop=400');assert main.evaluate('e=>e.scrollTop')>0 and sidebar.bounding_box()['y']==y and page.evaluate('window.scrollY')==0
 page.set_viewport_size({'width':720,'height':540});y=sidebar.bounding_box()['y'];main.evaluate('e=>e.scrollTop=550');assert sidebar.bounding_box()['y']==y
 row=page.locator('.recordingCard').first;t=row.locator('.recordingTime').bounding_box();a=row.locator('.rowActions').bounding_box();assert a['x']-(t['x']+t['width'])<30
 assert row.get_by_role('img',name='Anteprima disponibile').count()==1
 page.evaluate('sdStart(0)');page.wait_for_selector('#sdInternalPanel[open]');assert page.locator('#sdInternalVideo').get_attribute('src').endswith('.m3u8');assert calls[-1]['target']=='internal';page.keyboard.press('Escape');page.wait_for_selector('#sdInternalPanel',state='hidden');assert len(stops)==1
 page.evaluate("showView('library')");page.wait_for_selector('.tile');page.evaluate('openMediaPanel('+json.dumps(stem)+')');page.wait_for_function("document.getElementById('mediaInfo').textContent.includes('Intervalli di movimento')")
 page.get_by_role('button',name='Riproduci dalla SD').click();page.wait_for_selector('#sdInternalPanel[open]');assert calls[-1]['action']=='play' and not page.locator('#mediaPanel').is_visible()
 page.locator('#sdInternalPanel').locator('button[onclick="sdStop()"]').click();page.wait_for_selector('#sdInternalPanel',state='hidden');assert len(stops)==2
 assert not errors,errors
 browser.close();print('PASS sidebar coordinates on scroll, compact rows, icons, motion count, SD from both views and stop by Escape/close')
