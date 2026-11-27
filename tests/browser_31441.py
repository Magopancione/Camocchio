import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app
calls=[];stops=[];errors=[];live_calls=[]
stem='V380_2026-11-24_12-00-00'
local='V380_2026-11-24_12-02-00';single=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,**({'executable_path':os.environ['BROWSER_PATH']} if os.environ.get('BROWSER_PATH') else {}))
 page=browser.new_page(viewport={'width':1200,'height':680});page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  path=r.request.url.split('http://test.local')[-1].split('?')[0]
  if path=='/':return r.fulfill(body=app.HTML,content_type='text/html')
  data={'ok':1}
  if path=='/api/config':data={'has_password':True,'host':'camera.test','camera_name':'Ingresso','device_id':123,'sd_target':'internal','preview_mode':'uniform'}
  if path=='/api/list':data={'items':[{'start':f'{6+i//3:02}:{(i*19)%60:02}:00','end':f'{6+i//3:02}:{(i*19)%60:02}:45','downloaded':i==1,'preview':i in (0,1),'preview_kind':'motion' if i==0 else 'uniform','motion_count':5 if i==0 else None,'local_stem':stem if i==0 else None} for i in range(40)]}
  if path=='/api/library':data={'items':[{'name':stem,'thumb':'a.gif','video':None,'preview_kind':'motion','motion_count':3,'date':'24-11-2026'},{'name':local,'thumb':'new.gif' if single else None,'video':local+'.mp4','preview_kind':'uniform','date':'24-11-2026'}]}
  if path=='/api/preview-info':data={'preview':{'filename':'a.gif','bytes':1000,'path':'/test/a.gif','modified':'2026-11-24T12:00:00','report':{'mode':'motion','events':[[1,2],[4,5],[10,11]]}}}
  if path in ('/api/sd-playback-start','/api/gallery-sd'):calls.append(r.request.post_data_json);data={'target':'internal'}
  if path.startswith('/api/live') or path=='/api/test-protocol-8800':live_calls.append((path,r.request.post_data_json if r.request.method=='POST' else None))
  if path=='/api/test-protocol-8800':data={'authenticated':True,'message':'Autenticazione riuscita; Live non verificato'}
  if path=='/api/live-av-status':data={'running':False,'ready':False,'audio':False,'error':'Fine fixture'}
  if path=='/api/thumbnail-missing':single.append(r.request.post_data_json);data={'ok':True,'created':True}
  if path=='/api/preview-batch-status':data={'running':False,'message':'2 create'}
  if path=='/api/sd-playback-stop':stops.append(True)
  if path=='/api/sd-playback-status':data={'running':False,'message':'Pronto','playlist':'/sd-hls/sample/index.m3u8'} if len(calls)>len(stops) else {'running':False,'message':'Fermo'}
  if path=='/assets/app-icon.png':return r.fulfill(path=str(Path(app.__file__).with_name('app-icon.png')),content_type='image/png')
  if path.startswith(('/media/','/assets/','/sd-hls/')):return r.fulfill(status=404)
  r.fulfill(body=json.dumps(data),content_type='application/json')
 page.route('http://test.local/**',route);page.goto('http://test.local/');page.wait_for_selector('.recordingCard')
 sidebar=page.locator('.shell>aside');main=page.locator('.shell>main');y=sidebar.bounding_box()['y'];main.evaluate('e=>e.scrollTop=400');assert main.evaluate('e=>e.scrollTop')>0 and sidebar.bounding_box()['y']==y and page.evaluate('window.scrollY')==0
 page.set_viewport_size({'width':720,'height':540});y=sidebar.bounding_box()['y'];main.evaluate('e=>e.scrollTop=550');assert sidebar.bounding_box()['y']==y
 page.set_viewport_size({'width':1280,'height':820});main.evaluate('e=>e.scrollTop=0')
 row=page.locator('.recordingCard').first;t=row.locator('.recordingTime').bounding_box();a=row.locator('.rowActions').bounding_box();st=row.locator('.recordingStates').bounding_box();assert t['x']+t['width']<st['x'] and st['x']+st['width']<a['x']
 assert abs(row.locator('.stateIcons').bounding_box()['x']-page.locator('.recordingCard').nth(1).locator('.stateIcons').bounding_box()['x'])<1
 assert not page.locator('.playbackSummary').is_visible() and not page.locator('.sdDiagnostics').is_visible()
 assert page.locator('#nativeTitlebar .windowGrip').count()==1 and page.locator('#nativeTitlebar .customWindowTitle').count()==0
 assert row.locator('.recordingStatusIcon').first.bounding_box()['width']==38
 button=page.get_by_role('button',name='Scarica giornata',exact=True);button.hover();tip=page.locator('#appTooltip');assert tip.is_visible() and tip.inner_text()=='Scarica giornata' and tip.bounding_box()['x']>=8
 page.keyboard.press('Escape');assert not tip.is_visible()
 page.evaluate('settings.showModal()');a=page.locator('#device_id').bounding_box();b=page.locator('#password').bounding_box();assert abs(a['y']-b['y'])<1 and a['height']==b['height']==40;page.evaluate('settings.close()')
 assert row.get_by_role('img',name='Anteprima Parti significative').count()==1
 assert row.locator('.motionCount svg').count()==5 and row.locator('.sdAsset img').evaluate('(img)=>img.complete && img.naturalWidth>0')
 assert page.locator('.recordingCard').nth(1).locator('.macStatus:not(.noLocal)').count()==1
 assert page.locator('aside > .colorChooser:last-child').count()==1 and page.locator('label[for=day]').inner_text()=='DATA'
 assert page.locator('.recordingCard').nth(1).get_by_role('img',name='Anteprima Uniforme').count()==1
 page.get_by_role('button',name='Sul Mac',exact=True).click();assert page.locator('.recordingCard').count()==1 and page.locator('.recordingCard').get_attribute('data-index')=='1'
 page.locator('.eventMark').first.evaluate('el=>el.click()');assert page.locator('.recordingCard').count()==40 and page.locator('.captureFilters button').first.get_attribute('aria-pressed')=='true'
 main.evaluate('e=>e.scrollTop=0')
 if os.environ.get('CAMOCCHIO_RENDER'):page.screenshot(path=os.environ['CAMOCCHIO_RENDER'])
 page.evaluate('sdStart(0)');page.wait_for_selector('#sdInternalPanel[open]');assert page.locator('#sdInternalVideo').get_attribute('src').endswith('.m3u8');assert calls[-1]['target']=='internal';page.keyboard.press('Escape');page.wait_for_selector('#sdInternalPanel',state='hidden');assert len(stops)==1
 page.locator('.colorChooser summary').click();assert page.locator('#palette').is_visible();page.keyboard.press('Escape');assert not page.locator('#palette').is_visible()
 page.evaluate("showView('library')");page.wait_for_selector('.tile');page.locator('#previewBatchStart').click();page.locator('#batchConfirm').click();page.wait_for_function("document.getElementById('previewBatchState').textContent==='2 create'");assert page.locator('.cardTitleRow .cardIndicators .sdAsset').count()==1 and page.locator('.tile .motionCount').count()==0;page.evaluate('openMediaPanel('+json.dumps(stem)+')');page.wait_for_function("document.getElementById('mediaInfo').textContent.includes('Intervalli di movimento')")
 page.get_by_role('button',name='Riproduci dalla SD').click();page.wait_for_selector('#sdInternalPanel[open]');assert calls[-1]['action']=='play' and not page.locator('#mediaPanel').is_visible()
 page.locator('#sdInternalPanel').locator('button[onclick="sdStop()"]').click();page.wait_for_selector('#sdInternalPanel',state='hidden');assert len(stops)==2
 localcard=page.locator('.tile[data-stem="'+local+'"]');missing=localcard.locator('.thumbph');icon=localcard.locator('.macAsset img');assert icon.evaluate('i=>i.complete&&i.naturalWidth>0') and icon.bounding_box()['width']==33
 missing.hover();page.mouse.move(2,2);page.wait_for_timeout(800);assert not single
 missing.hover();page.wait_for_selector('.tile[data-stem="'+local+'"] img.thumb');assert single==[{'name':local+'.mp4'}]
 localcard.locator('img.thumb').hover();page.wait_for_timeout(750);assert len(single)==1
 assert page.locator('#liveSource').input_value()=='native'
 page.evaluate("showView('liveSection')")
 assert page.locator('#liveSource option').count()==2
 page.locator('#liveQuality').select_option('high')
 page.evaluate("liveStart()")
 page.evaluate("""()=>{const v=document.getElementById('liveVideo');const range={length:1,start:()=>0,end:()=>45};const buffer={length:1,start:()=>0,end:()=>21};Object.defineProperties(v,{seekable:{value:range},buffered:{value:buffer},readyState:{value:2},currentTime:{value:10,writable:true}});document.getElementById('liveTransport').hidden=false;updateTransport(v,true)}""")
 assert page.evaluate("transportStats(document.getElementById('liveVideo')).ahead")==11
 page.locator('#liveTransport select').select_option('4');assert page.evaluate("document.getElementById('liveVideo').playbackRate")==4
 page.locator('#liveTransport [data-step="30"]').click();assert page.evaluate("document.getElementById('liveVideo').currentTime")==40
 assert page.locator('#liveTransport [data-step="10"]').is_disabled()
 page.locator('#liveTransport [data-edge]').click();assert page.evaluate("document.getElementById('liveVideo').currentTime")==43.5 and page.evaluate("document.getElementById('liveVideo').playbackRate")==1
 page.locator('#liveSection details summary').click();page.locator('#observedLag').fill('8');page.locator('#observedAV').fill('-0.2');page.locator('#prepareLiveReport').click()
 report=json.loads(page.locator('#liveReport').input_value());assert report['ritardo_scena_misurato_s']==8 and report['scarto_audio_video_misurato_s']==-.2 and 'url' not in report
 assert ('/api/live-av-start',{'native':True,'quality':'high'}) in live_calls and not any(p=='/api/test-protocol-8800' for p,_ in live_calls)
 assert page.locator('#rtspOptional').is_hidden()
 page.locator('#liveSource').select_option('rtsp');assert page.locator('#rtspOptional').is_visible()
 page.evaluate('liveStart()');assert ('/api/live-av-start',{}) in live_calls
 assert not errors,errors
 browser.close();print('PASS sidebar coordinates on scroll, compact rows, icons, motion count, SD from both views and stop by Escape/close')
