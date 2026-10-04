import marshal, dis
src = open(r"C:\Users\Administrator\Downloads\low_on_fun.py", encoding="latin-1").read()
ns = {}
exec(compile(src.split("\n",1)[1].split("def replacer")[0], "hdr", "exec"), ns)
parts = ns["functions"].split(b"DELIM")
k = int(__import__("sys").argv[1])
dis.dis(marshal.loads(parts[k]), depth=0)
