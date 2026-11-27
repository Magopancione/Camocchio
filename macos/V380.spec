# Executed by PyInstaller on macOS only. Native architecture of build host.
from pathlib import Path
import shutil
ROOT=Path(SPECPATH).parent
src=ROOT/'src'
binaries=[]
for name in ('ffmpeg','ffprobe'):
    found=shutil.which(name)
    if not found:raise SystemExit(name+' assente sul Mac di compilazione')
    binaries.append((str(Path(found).resolve()),'bin'))
a=Analysis([str(src/'desktop.py')],pathex=[str(src)],binaries=binaries,
    datas=[(str(src/'languages.json'),'.'),(str(src/'app-icon.png'),'.'),(str(src/'refresh_icon.jpg'),'.'),(str(ROOT/'build-notices'),'ThirdPartyNotices')],
    hiddenimports=['app','live_av','sd_playback','motion_preview','local_media','webview.platforms.cocoa','PyObjCTools.AppHelper'],
    hookspath=[],runtime_hooks=[],excludes=[])
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Camocchio',debug=False,strip=False,upx=False,console=False,
        argv_emulation=False,codesign_identity=None,entitlements_file=None)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='Camocchio')
app=BUNDLE(coll,name='Camocchio.app',icon=str(src/'AppIcon.icns'),bundle_identifier='local.v380mac',
    info_plist={'CFBundleShortVersionString':'3.14.42','CFBundleVersion':'3.14.42',
                'NSHighResolutionCapable':True,
                'NSLocalNetworkUsageDescription':'Connessione alla telecamera locale per Live e registrazioni microSD.',
                'NSAppTransportSecurity':{'NSAllowsLocalNetworking':True,'NSAllowsArbitraryLoadsForMedia':True}})
