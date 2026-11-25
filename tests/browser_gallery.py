import sys,threading,json,ast
from pathlib import Path
from playwright.sync_api import sync_playwright
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'src'));import app
# Stub all camera and filesystem API data in browser. No real device accessed.
items=[dict(name='V380_2026-11-22_13-52-17',label='N.7 del: 22-11-2026 ore: 13:52:17 - 13:54:17',video='V380_2026-11-22_13-52-17.mp4',thumb='a.gif',size=1000,preview_kind='motion',preview_tip='Parti significative',date='22-11-2026'),dict(name='V380_2026-11-13_12-35-38',label='N.2 del: 13-11-2026 ore: 12:35:38',video=None,thumb='b.gif',preview_kind='uniform',preview_tip='Uniforme',date='13-11-2026')]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,**({'executable_path':__import__('os').environ['BROWSER_PATH']} if __import__('os').environ.get('BROWSER_PATH') else {}));page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(req):
  path=req.request.url.split('http://test.local')[-1].split('?')[0]
  if path=='/':req.fulfill(body=app.HTML,content_type='text/html');return
  if path=='/api/config':data={'has_password':True,'host':'camera.test','device_id':0,'username':'','preview_mode':'uniform','library_page_size':12,'palette':'green'}
  elif path=='/api/list':data={'items':[{'start':'12:00:00','end':'12:02:00','downloaded':True,'preview':True,'local_stem':items[0]['name']}]} 
  elif path=='/api/library':data={'items':items}
  elif path=='/api/preview-info':data={'preview':{'filename':'b.gif','bytes':12345,'path':'/test/b.gif','modified':'2026-11-22T17:00:00','report':{'mode':'uniform','interval':[1,119.999633]},'probe':{'streams':[{'width':480,'height':270,'nb_read_frames':'30'}],'format':{'duration':'6.90'}}}}
  elif path=='/api/gallery-sd':data={'ok':1}
  elif path=='/api/sd-playback-status':data={'running':False,'message':'Test','bytes':0}
  elif path.startswith('/media/') or path.startswith('/assets/'):
   req.fulfill(status=404);return
  else:data={'ok':1}
  req.fulfill(body=json.dumps(data),content_type='application/json')
 page.route('http://test.local/**',route);page.goto('http://test.local/');page.wait_for_selector('.recordingCard')
 assert page.locator('#recordings').is_visible() and not page.locator('#library').is_visible() and not page.locator('#liveSection').is_visible()
 assert page.locator('aside #day').count()==1
 assert page.locator('.recordingCard .progressBadge').inner_text()=='100%'
 assert page.get_by_role('button',name='Apri video locale',exact=True).is_visible()
 assert page.get_by_role('button',name='Riproduci dalla microSD',exact=True).count()==0
 assert page.locator('.recordingHead #refreshBtn').count()==1
 page.locator('.colorChooser summary').click();page.locator('#palette').select_option('teal');assert not page.locator('.colorChooser').evaluate('(e)=>e.open')
 page.locator('.colorChooser summary').click();page.locator('.recordingHead h2').click();assert not page.locator('.colorChooser').evaluate('(e)=>e.open')
 page.locator('.colorChooser summary').click();page.keyboard.press('Escape');assert not page.locator('.colorChooser').evaluate('(e)=>e.open')
 page.locator('.recordingCard').click();page.wait_for_selector('.tile');assert page.locator('#library').is_visible() and not page.locator('#recordings').is_visible()
 page.locator('.tile').nth(1).locator('.thumb').click();page.wait_for_function("document.getElementById('mediaInfo').textContent.includes('Fotogrammi')")
 assert page.get_by_role('button',name='Riproduci dalla SD',exact=True).is_visible()
 page.locator('#mediaPanel').evaluate('(e)=>e.close()')
 page.locator('aside nav .nav').nth(3).click()
 assert page.locator('[data-settings-page=camera]').is_visible()
 for key in ['preview','playback','storage','interface']:
  page.locator('[data-settings-tab='+key+']').click();assert page.locator('[data-settings-page='+key+']').is_visible()
 assert page.locator('#settings #sd_stream_audio').count()==1
 assert page.locator('#settings #save_dir').count()==1
 page.locator('[data-settings-tab=preview]').click();page.locator('#preview_mode').select_option('motion');assert page.locator('#preview_frames').input_value()=='30'
 page.locator('#settings').evaluate('(e)=>e.close()')
 page.locator('aside nav .nav').nth(0).click();assert page.locator('#liveSection').is_visible() and not page.locator('#library').is_visible()
 assert not errors,errors
 browser.close();print('PASS: circuit cards, 100%, local actions, sidebar date, view switching, settings categories, palette auto-close, no JS errors')
