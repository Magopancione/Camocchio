from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "dist" / "V380 Mac 3.14.23.app"
if DEST.exists():
    shutil.rmtree(DEST)
(DEST / "Contents/MacOS").mkdir(parents=True)
shutil.copytree(ROOT / "src", DEST / "Contents/Resources", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copy2(ROOT / "macos/Info.plist", DEST / "Contents/Info.plist")
shutil.copy2(ROOT / "macos/launcher", DEST / "Contents/MacOS/launcher")
(DEST / "Contents/MacOS/launcher").chmod(0o755)
print(DEST)
