"""Loopback fixture for the existing camera login, no real camera or password."""
import socket,struct,sys,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import app

def exercise(reply):
 received=[]
 with socket.socket() as server:
  server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(2)
  def handle():
   conn,_=server.accept()
   with conn:
    conn.settimeout(2);received.append(app.exact(conn,520));conn.sendall(reply)
  t=threading.Thread(target=handle);t.start()
  address=server.getsockname();dial=socket.create_connection
  with patch.object(app,'runtime',return_value={'host':'camera.invalid','port':8800,'device_id':123,'username':'123','password':'test-only'}),patch.object(app,'env',return_value=bytes(64)),patch.object(app.socket,'create_connection',side_effect=lambda target,timeout:dial(address,2)) as connect:
   result=app.test_protocol_8800();assert connect.call_args.args[0]==('camera.invalid',8800)
  t.join(3);assert not t.is_alive();assert len(received)==1 and struct.unpack_from('<I',received[0])[0]==1167
  assert 'ticket' not in result and 'test-only' not in str(result)
  assert not app.JOB_LOCK.locked();return result

def reply(code):
 b=bytearray(256);struct.pack_into('<Ii',b,0,1168,code);b[12]=31;struct.pack_into('<I',b,13,999);return b
assert exercise(reply(1001))['authenticated']
assert not exercise(reply(1000))['authenticated']
assert not exercise(bytes(12))['authenticated']
with patch.object(app,'runtime',return_value={'port':8800}),patch.object(app,'login',side_effect=socket.timeout):
 assert not app.test_protocol_8800()['authenticated'] and not app.JOB_LOCK.locked()
with app.JOB_LOCK,patch.object(app,'login') as login:
 try:app.test_protocol_8800();raise AssertionError('busy guard missing')
 except RuntimeError:pass
 login.assert_not_called()
assert exercise(reply(1001))['authenticated']
print('PASS TCP 8800: loopback login request, accepted/rejected/truncated replies, timeout, busy guard and retry; no media commands')
