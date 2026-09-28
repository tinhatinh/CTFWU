"""Streaming Zstandard decoder via ctypes against Git for Windows' libzstd.dll.

Zero-install: no pip packages, no zstd CLI. Reads the compressed file in chunks and
streams the decompressed bytes to the output path.

usage: python zstd_ctypes.py <input.zst> <output>
"""

import ctypes
import os
import sys

DLL_CANDIDATES = [
    r"C:\Program Files\Git\mingw64\bin\libzstd.dll",
    r"C:\Program Files\Git\usr\bin\msys-zstd-1.dll",
    r"C:\Program Files\Tesseract-OCR\libzstd.dll",
]

CHUNK_IN = 1 << 20
CHUNK_OUT = 8 << 20
PTR = ctypes.c_void_p


class InBuffer(ctypes.Structure):
    _fields_ = [("src", PTR), ("size", ctypes.c_size_t), ("pos", ctypes.c_size_t)]


class OutBuffer(ctypes.Structure):
    _fields_ = [("dst", PTR), ("size", ctypes.c_size_t), ("pos", ctypes.c_size_t)]


def load():
    for path in DLL_CANDIDATES:
        if not os.path.exists(path):
            continue
        d = ctypes.CDLL(path)
        d.ZSTD_versionString.restype = ctypes.c_char_p
        d.ZSTD_createDCtx.restype = PTR
        d.ZSTD_freeDCtx.argtypes = [PTR]
        d.ZSTD_decompressStream.argtypes = [PTR, ctypes.POINTER(OutBuffer), ctypes.POINTER(InBuffer)]
        d.ZSTD_decompressStream.restype = ctypes.c_size_t
        d.ZSTD_isError.argtypes = [ctypes.c_size_t]
        d.ZSTD_isError.restype = ctypes.c_uint
        d.ZSTD_getErrorName.restype = ctypes.c_char_p
        return d
    raise SystemExit("[-] no libzstd.dll found on this machine")


def decompress(src, dst):
    d = load()
    print(f"[*] libzstd {d.ZSTD_versionString().decode()}")
    ctx = d.ZSTD_createDCtx()
    if not ctx:
        raise SystemExit("[-] ZSTD_createDCtx failed")

    in_buf = ctypes.create_string_buffer(CHUNK_IN)
    out_buf = ctypes.create_string_buffer(CHUNK_OUT)
    total_in = total_out = frames = 0

    try:
        with open(src, "rb") as f, open(dst, "wb") as g:
            while True:
                n = f.readinto(in_buf)
                if not n:
                    break
                ib = InBuffer(ctypes.cast(in_buf, PTR), n, 0)
                while ib.pos < n:
                    ob = OutBuffer(ctypes.cast(out_buf, PTR), CHUNK_OUT, 0)
                    r = d.ZSTD_decompressStream(ctx, ctypes.byref(ob), ctypes.byref(ib))
                    if d.ZSTD_isError(r):
                        raise SystemExit(f"[-] error at out {total_out}: {d.ZSTD_getErrorName(r).decode()}")
                    if ob.pos:
                        g.write(out_buf[: ob.pos])
                        total_out += ob.pos
                    if r == 0:
                        frames += 1
                        print(f"[+] frame {frames} complete, {total_out:,} bytes so far", flush=True)
                    if ob.pos == 0 and r != 0 and ib.pos >= n:
                        break
                total_in += n
                if total_in % (128 << 20) < CHUNK_IN:
                    print(f"    {total_in >> 20} MiB in -> {total_out >> 20} MiB out", flush=True)
    finally:
        d.ZSTD_freeDCtx(ctx)
    print(f"[+] done: {total_in:,} in -> {total_out:,} out ({frames} frame(s))")
    return total_out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python zstd_ctypes.py <input.zst> <output>")
    decompress(sys.argv[1], sys.argv[2])
