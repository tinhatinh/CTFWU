import ctypes,io,os,sys,tarfile
Z=ctypes.CDLL(r"C:\Program Files\Git\mingw64\bin\libzstd.dll")
class InB(ctypes.Structure): _fields_=[("src",ctypes.c_void_p),("size",ctypes.c_size_t),("pos",ctypes.c_size_t)]
class OutB(ctypes.Structure): _fields_=[("dst",ctypes.c_void_p),("size",ctypes.c_size_t),("pos",ctypes.c_size_t)]
mk=Z.ZSTD_createDCtx; mk.restype=ctypes.c_void_p
fr=Z.ZSTD_freeDCtx; fr.argtypes=[ctypes.c_void_p]
ie=Z.ZSTD_isError; ie.argtypes=[ctypes.c_size_t]; ie.restype=ctypes.c_uint
fn=Z.ZSTD_decompressStream
fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(InB),ctypes.POINTER(OutB)]
fn.restype=ctypes.c_size_t
def zstd(raw):
    d=mk(); out=bytearray(); CH=1<<20; pos=0
    try:
        while pos<len(raw):
            src=ctypes.create_string_buffer(raw[pos:],len(raw)-pos)
            buf=ctypes.create_string_buffer(CH)
            ib=InB(); ib.src=ctypes.addressof(src); ib.size=len(raw)-pos; ib.pos=0
            ob=OutB(); ob.dst=ctypes.addressof(buf); ob.size=CH; ob.pos=0
            r=fn(d,ctypes.byref(ib),ctypes.byref(ob))
            if ie(r): raise RuntimeError("zstd error %d"%r)
            out+=buf.raw[:ob.pos]; pos+=ib.pos
            if r==0: break
    finally: fr(d)
    return bytes(out)
if __name__=="__main__":
    for path in sys.argv[1:]:
        tar=zstd(open(path,'rb').read())
        tf=tarfile.open(fileobj=io.BytesIO(tar))
        nm=[x for x in tf.getnames() if x.endswith("libc-2.so") or x.endswith("libc.so.6")]
        data=tf.extractfile(nm[0]).read()
        out=os.path.join(os.path.dirname(path),"libc.so.6")
        open(out,"wb").write(data)
        print("[+]",out,len(data),"bytes")
