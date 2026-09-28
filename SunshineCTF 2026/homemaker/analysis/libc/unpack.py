import ctypes, os, subprocess, sys, tarfile, io
Z = ctypes.CDLL(r"C:\Program Files\Git\mingw64\bin\libzstd.dll")
Z.ZSTD_isError.restype = ctypes.c_size_t
Z.ZSTD_createDCtx.restype = ctypes.c_void_p
Z.ZSTD_decompressStream.restype = ctypes.c_size_t
Z.ZSTD_freeDCtx.argtypes = [ctypes.c_void_p]
class Buf(ctypes.Structure):
    _fields_=[("src",ctypes.c_char_p),("size",ctypes.c_size_t),("pos",ctypes.c_size_t),
              ("dst",ctypes.c_char_p),("dstCapacity",ctypes.c_size_t),("dstPos",ctypes.c_size_t),
              ("reservedSize",ctypes.c_size_t)]
Z.ZSTD_initDStream.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t]
def zstd_decompress(data):
    dctx=Z.ZSTD_createDCtx(); out=bytearray(); CHUNK=1<<20
    try:
        pos=0
        while pos < len(data):
            dst=ctypes.create_string_buffer(CHUNK)
            inb=Buf(); inb.src=data[pos:]; inb.size=len(data)-pos; inb.pos=0
            inb.dst=dst; inb.dstCapacity=CHUNK; inb.dstPos=0
            r=Z.ZSTD_decompressStream(dctx, ctypes.byref(inb), ctypes.byref(inb))
            if Z.ZSTD_isError(r): raise RuntimeError("zstd err at offset %d"%pos)
            out += inb.dst.raw[:inb.dstPos] if hasattr(inb.dst,'raw') else bytes(inb)[:inb.dstPos]
            pos += inb.pos
            if r==0: break
    finally:
        Z.ZSTD_freeDCtx(dctx)
    return bytes(out)
for deb in sys.argv[1:]:
    tag=deb.split("_")[0]+"_"+deb.split("_")[1]
    d="x_"+tag.replace(".","_")
    os.makedirs(d,exist_ok=True)
    subprocess.run(["7z","x","-y","-o"+d,deb],check=True,capture_output=True)
    zst=[os.path.join(d,x) for x in os.listdir(d) if x.endswith(".tar.zst")]
    if not zst: print("no zst in",deb,os.listdir(d)); continue
    raw=open(zst[0],'rb').read()
    tar=zstd_decompress(raw)
    open(os.path.join(d,"data.tar"),"wb").write(tar)
    tf=tarfile.open(fileobj=io.BytesIO(tar))
    for nm in tf.getnames():
        if nm.endswith("/libc-2.*.so") or nm.endswith("libc.so.6"):
            data=tf.extractfile(nm).read()
            out=os.path.join(d,"libc.so.6"); open(out,"wb").write(data)
            print("[+] %s -> %s (%d bytes)"%(tag,nm,len(data)))
            break
