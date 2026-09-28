import re, itertools
lines=open(__import__('sys').argv[1] if len(__import__('sys').argv)>1 else 'files/suntrail.klc',encoding='utf-8').read().split('\n')
keys={}
for l in lines:
    f=l.split('\t')
    if len(f)==6 and re.fullmatch(r'[0-9a-f]{2}',f[0]):
        keys[f[1]]=(int(f[0],16), chr(int(f[3],16)), chr(int(f[4],16)))
def rows(lo,hi): return sorted([k for k in keys if lo<=keys[k][0]<=hi], key=lambda k:keys[k][0])
grid={}
for r,row in enumerate([rows(0x10,0x14),rows(0x1E,0x23),rows(0x2C,0x31)]):
    for c,k in enumerate(row): grid[k]=(r,c)
NEIGH=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
GLYPHS=['\u2192','\u2196','\u2198']
def walk(assign,start):
    seq,cur,seen=[],start,set()
    while cur and cur not in seen:
        seen.add(cur); seq.append(cur)
        g=keys[cur][1]
        if g=='\u25a0': return seq,'GOAL'
        if g not in assign: return seq,'STOP'
        r,c=grid[cur]; off=assign[g]
        cur=next((k for k,(rr,cc) in grid.items() if (rr,cc)==(r+off[0],c+off[1])), None)
    return seq,'CYCLE'
for combo in itertools.product(NEIGH,repeat=3):
    a=dict(zip(GLYPHS,combo))
    for st in keys:
        seq,tag=walk(a,st)
        s=''.join(keys[k][2] for k in seq)
        if '{' in s and '}' in s:
            print(tag, st, ''.join(seq), repr(s), combo)
