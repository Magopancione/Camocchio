"""Browser integration with simulated APIs; no camera is contacted."""
import json,os,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,**({'executable_path':os.environ['BROWSER_PATH']} if os.environ.get('BROWSER_PATH') else {}))
    page=browser.new_page(viewport={'width':1280,'height':850}); errors=[]; calls=[]
    configured=True; active=False; failed=False
    page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
        global active
        path=r.request.url.split('http://test.local')[-1].split('?')[0]
        if path=='/':return r.fulfill(body=app.HTML,content_type='text/html')
        if path.startswith('/assets/'):
            if path=='/assets/languages.json':return r.fulfill(path=str(Path(app.__file__).with_name('languages.json')))
            if path=='/assets/app-icon.png':return r.fulfill(path=str(Path(app.__file__).with_name('app-icon.png')))
            return r.fulfill(status=404)
        body=r.request.post_data_json if r.request.method=='POST' else None
        calls.append((path,body))
        data={'ok':1}
        if path=='/api/config':data={'host':'camera.test','device_id':123,'has_password':configured,'live_quality':'low','palette':'blue'}
        elif path=='/api/library':data={'items':[]}
        elif path=='/api/list':
            assert not active
            data={'items':[{'start':'07:01:56','end':'07:03:56','downloaded':False,'preview':False}]}
        elif path=='/api/live-av-start':active=True
        elif path=='/api/live-av-stop':active=False
        elif path=='/api/live-av-status':data={'running':active,'ready':False,'audio':False,'error':'Errore di prova' if failed else ''}
        r.fulfill(body=json.dumps(data),content_type='application/json')
    page.route('http://test.local/**',route);page.goto('http://test.local/')
    page.wait_for_function("document.getElementById('liveToggle').textContent.includes('Ferma')")
    assert page.locator('#liveSection').is_visible() and page.locator('#recordings').is_hidden()
    assert page.locator('[data-quality=high]').get_attribute('aria-pressed')=='true'
    assert [b for p,b in calls if p=='/api/live-av-start']==[{'native':True,'quality':'high'}]
    assert not any(p=='/api/list' for p,b in calls)
    assert page.locator('#liveBadges').is_hidden()
    page.locator('[data-quality=low]').click();page.wait_for_timeout(200)
    assert [b for p,b in calls if p=='/api/live-av-start'][-1]=={'native':True,'quality':'low'}
    page.locator('[data-source=rtsp]').click();page.wait_for_timeout(200)
    assert page.locator('#liveQualityWrap').is_hidden() and page.locator('#rtspOptional').is_visible()
    assert [b for p,b in calls if p=='/api/live-av-start'][-1]=={}
    page.locator('[data-source=native]').click();page.wait_for_timeout(200)
    assert page.locator('#liveQualityWrap').is_visible()
    assert [b for p,b in calls if p=='/api/live-av-start'][-1]=={'native':True,'quality':'low'}
    page.evaluate("""()=>{const v=document.getElementById('liveVideo');const range={length:1,start:()=>0,end:()=>45};const buffer={length:1,start:()=>0,end:()=>21};Object.defineProperties(v,{seekable:{value:range},buffered:{value:buffer},readyState:{value:2},currentTime:{value:10,writable:true}});updateTransport(v,true)}""")
    assert page.evaluate("transportStats(document.getElementById('liveVideo')).ahead")==11
    page.locator('[data-rate="2"]').click();assert page.evaluate("document.getElementById('liveVideo').playbackRate")==2
    page.locator('#liveTransport [data-step="30"]').click();assert page.evaluate("document.getElementById('liveVideo').currentTime")==40
    assert page.locator('#liveTransport [data-step="10"]').is_disabled()
    page.locator('#liveTransport [data-edge]').click();assert page.evaluate("document.getElementById('liveVideo').currentTime")==43.5 and page.evaluate("document.getElementById('liveVideo').playbackRate")==1
    assert page.locator('#liveRates button').all_inner_texts()==['1×','2×']
    assert page.locator('#sdInternalVideoTransport select option').all_inner_texts()==['1×','2×']
    page.locator('#liveSection details summary').click();page.locator('#observedLag').fill('8');page.locator('#observedAV').fill('-0.2');page.locator('#prepareLiveReport').click()
    report=json.loads(page.locator('#liveReport').input_value());assert report['ritardo_scena_misurato_s']==8 and report['scarto_audio_video_misurato_s']==-.2 and 'url' not in report
    page.locator('[data-view=recordings]').click();page.wait_for_selector('.recordingCard');assert not active
    assert '07:01:56' in page.locator('.recordingTime').inner_text()
    assert page.locator('.eventMark').get_attribute('title').startswith('07:01:56')
    page.locator('[data-view=liveSection]').click();assert page.locator('#liveToggle').inner_text().endswith('Avvia Live')
    page.set_viewport_size({'width':720,'height':540});assert page.locator('#liveSection').evaluate('e=>e.scrollWidth<=e.clientWidth')
    failed=True;page.locator('#liveToggle').click();page.wait_for_function("document.getElementById('liveState').textContent.includes('Errore di prova')")
    assert page.locator('#liveBadges').is_hidden();page.locator('#liveToggle').click()
    configured=False;calls.clear();page.reload();page.wait_for_selector('#settings[open]')
    assert not any(p=='/api/live-av-start' for p,b in calls)
    assert not errors,errors
    browser.close();print('PASS: startup TCP 8800 High, reselect, RTSP, buffer controls, diagnostics, stop before SD, error state and missing setup')
