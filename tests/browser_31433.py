import sys,json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));import app
items=[dict(name='V380_2026-11-24_12-00-00',label='N.1 del: 24-11-2026 ore: 12:00:00',video='V380_2026-11-24_12-00-00.mp4',thumb='a.gif',size=1000,preview_kind='motion',preview_tip='Parti significative',date='24-11-2026')]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/opt/pw-browsers/chromium-1228/chrome-linux64/chrome');page=browser.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(req):
  path=req.request.url.split('http://test.local')[-1].split('?')[0]
  if path=='/':req.fulfill(body=app.HTML,content_type='text/html');return
  if path=='/api/config':data={'has_password':True,'host':'camera.test','device_id':123,'username':'123','preview_mode':'uniform','library_page_size':12,'palette':'purple','sd_target':'internal'}
  elif path=='/api/list':data={'items':[{'start':'12:00:00','end':'12:02:00','downloaded':False,'preview':False,'local_stem':None}]}
  elif path=='/api/library':data={'items':items}
  elif path=='/api/live-av-status':data={'running':True,'ready':True,'audio':False,'error':'','warning':'','url':'/live-av/x/live.m3u8'}
  elif path=='/api/sd-playback-status':data={'running':False,'message':'Fermo','bytes':0}
  elif path.startswith('/media/') or path.startswith('/assets/'):req.fulfill(status=404);return
  else:data={'ok':1}
  req.fulfill(body=json.dumps(data),content_type='application/json')
 page.route('http://test.local/**',route);page.goto('http://test.local/');page.wait_for_selector('.recordingCard')
 assert page.title()=='Camocchio 3.14.33';assert page.locator('.customWindowTitle').inner_text()=='Camocchio'
 assert page.locator('[data-settings-tab=interface]').count()==0;assert page.locator('.mediaLegend').count()==0
 assert page.locator('.shell>aside').evaluate("e=>getComputedStyle(e).position")=='sticky'
 page.locator('aside nav .nav').nth(2).click();page.wait_for_selector('.tile');page.locator('.tile').first.locator('.thumb').click();page.wait_for_selector('#mediaPanel[open]')
 page.get_by_role('button',name='Elimina',exact=True).last.click();page.wait_for_selector('#deleteConfirmDialog[open]')
 assert page.locator('#deleteConfirmDialog').bounding_box()['height']<250
 assert page.locator('#mediaPanel').is_visible()
 page.locator('#deleteConfirmDialog button').first.click();assert not page.locator('#deleteConfirmDialog').is_visible()
 page.locator('#mediaPanel').evaluate('(e)=>e.close()');page.locator('aside nav .nav').nth(0).click();page.wait_for_selector('#liveSection:not([hidden])')
 page.evaluate('liveAVStart()');page.wait_for_timeout(200)
 assert page.locator('#liveAVMode').is_disabled();assert 'non contiene audio' in page.locator('#liveState').inner_text()
 assert not errors,errors
 browser.close();print('PASS Camocchio UI: title, fixed sidebar, removed interface/legend, compact deletion dialog, RTSP no-audio state')
