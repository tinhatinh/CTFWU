import os, socket, subprocess, sys

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", int(sys.argv[1]) if len(sys.argv) > 1 else 2324))
srv.listen(8)
print("listening", flush=True)

while True:
    c, _ = srv.accept()
    os.dup2(c.fileno(), 0)
    subprocess.Popen(["./ld-linux-x86-64.so.2", "--library-path", ".", "./ccu_premium"],
                     stdin=0, stdout=c.fileno(), stderr=c.fileno(), cwd="/lab").wait()
    c.close()
