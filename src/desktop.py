"""Native window entry point. Build on macOS, never run a shell launcher."""
import fcntl
import json
import os
import sys
import threading
from pathlib import Path


class WindowAPI:
    def __init__(self):self._window=None
    def window_action(self,action):
        from PyObjCTools import AppHelper
        def run():
            if action=='close':
                native=getattr(self._window,'native',None)
                if native is not None and hasattr(native,'performClose_'):native.performClose_(None)
                else:self._window.destroy()
            elif action=='minimize':self._window.minimize()
            elif action=='toggle-maximize':
                if self._window.maximized:self._window.restore()
                else:self._window.maximize()
        AppHelper.callAfter(run);return True


def main():
    import app
    import webview
    directory=Path.home()/'Library/Application Support/V380 Mac 2'
    directory.mkdir(parents=True,exist_ok=True)
    lock=(directory/'desktop.lock').open('a+')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        webview.create_window('Camocchio',html='<h3>V380 Mac è già aperto.</h3><p>Controlla la finestra esistente nel Dock.</p>',width=420,height=180)
        webview.start(gui='cocoa');return
    app.LOG.parent.mkdir(parents=True,exist_ok=True)
    output=app.LOG.open('a',buffering=1)
    sys.stdout=output;sys.stderr=output
    # LaunchServices PATH is not the Terminal PATH. Bundled tools are preferred by app.tool_path.
    os.environ['PATH']='/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
    server=app.ThreadingHTTPServer(('127.0.0.1',0),app.H)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    appearance=WindowAPI()
    colors={'purple':'#150728','green':'#06230d','magenta':'#350424','orange':'#401205','blue':'#041b3e','teal':'#032e32'}
    initial_color=colors.get(app.cfg().get('palette','purple'),'#150728')
    window=webview.create_window('Camocchio',f'http://127.0.0.1:{server.server_port}/',width=1280,height=850,min_size=(720,540),confirm_close=True,js_api=appearance,background_color=initial_color,frameless=True,easy_drag=False,shadow=True)
    appearance._window=window
    app.NATIVE_QUIT=window.destroy
    try:webview.start(gui='cocoa',debug=False,private_mode=True)
    finally:
        app.STOP_JOB.set();app.SD_PLAYBACK.stop();app.stop_live();app.LIVE_AV.stop()
        server.shutdown();server.server_close();thread.join(timeout=3)
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()


if __name__=='__main__':main()
