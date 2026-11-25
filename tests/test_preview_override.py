import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));import app
with tempfile.TemporaryDirectory() as td:
 gif=Path(td)/'test.gif';config={'preview_mode':'motion','preview_start':10,'preview_end':60,'preview_frames':50,'preview_seconds':10,'motion_frames':30,'motion_seconds':7}
 with patch.object(app,'cfg',return_value=config),patch.object(app,'makegif_uniform') as uniform:
  app.makegif(Path(td)/'test.mp4',gif,120,mode='uniform')
  assert uniform.call_args.args[3]['preview_mode']=='uniform'
  assert config['preview_mode']=='motion'
  assert json.loads(gif.with_suffix('.motion.json').read_text())['mode']=='uniform'
 with patch.object(app,'cfg',return_value=dict(config,preview_mode='uniform')),patch('motion_preview.generate') as generate,patch.object(app,'ffmpeg',return_value='ffmpeg'):
  app.makegif(Path(td)/'test.mp4',gif,120,mode='motion')
  assert generate.call_args.args[3]['preview_mode']=='motion'
 print('PASS: per-GIF mode override in both directions; no global settings mutation')
