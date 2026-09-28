"""Encoder 'dog whistle' cho bridge cua Aria.

Cau truc phan tich cua firmware:
  0x1940 EQ (flat)  -> 0x2550 AN TOAN: tu giai ma x  -> neu TLV type 1/2 : LOCKOUT
                    -> 0x1f70 x = P(x) = 0.98u+0.05u^2+0.005u^3, u = 4x
                    -> 0x1e30 ha sample 96k->16k  -> 0x2070 giai ma  -> 0x2790 dispatch

P(x) la da thuc khong tuyen => sinh tone tich. Ke so 16 kHz cua 0x2070 la Goertzel
200 sample, spacing 80 Hz dung bang bin cua DFT 200 diem, va cac tone dieu khien
800..2000 Hz = bin 10..25. Nen chon carrier o hai bin cao p,q (>=26, boi qua 2000 Hz
nên 0x2550 khong nhin thay) sao cho p-q = bin can may. Khi do:
  * x co nang luong hoan toan ngoai bin 10..25 -> 0x2550 giai ra rac -> an toan
  * P(x) chua tone hieu o bin 10..25 -> 0x2070 giai ra khung lenh that
Chon q = 51 de moi tich khac (2q-p = 51-B, p+q, 3p...) deu roi ngoai 10..25.
Moi symbol dung dung 1200 sample @96 kHz = 200 @16k, tan so la boi so cua 80 Hz
nên tron chu ky trong cua so phan tich (unh orthogonality).
"""
import base64
import math
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIC = 96000
UPS = 6
SYM16 = 200
SYM = SYM16 * UPS              # 1200
LEAD = 64 * UPS                 # 384
Q = 51                          # carrier co dinh (4080 Hz)


def frame_bytes(payload, pre=b"\xa5\x5a"):
    ln = len(payload) & 0xFF
    ck = ln
    for b in payload:
        ck ^= b
    return pre + bytes([ln]) + bytes(payload) + bytes([ck & 0xFF])


def nibbles(frame):
    out = []
    for b in frame:
        out.append((b >> 4) & 0xF)
        out.append(b & 0xF)
    return out


def symbol_carriers(nib, amp):
    """Hai sine o bin Q va Q+10+nib -> hieu tan = 800+80*nib."""
    m1 = Q
    m2 = Q + 10 + nib
    w1 = 2 * math.pi * m1 / SYM
    w2 = 2 * math.pi * m2 / SYM
    return [amp * math.sin(w1 * i) + amp * math.sin(w2 * i) for i in range(SYM)]


def symbol_direct(nib, amp):
    """Symbol truyen thong: mot tone o bin 10+nib (di qua duoc 0x2550)."""
    w = 2 * math.pi * (10 + nib) / SYM
    return [amp * math.sin(w * i) for i in range(SYM)]


def build(payload, amp=0.5, mode="whistle", pre=b"\xa5\x5a"):
    fr = frame_bytes(payload, pre)
    nib = nibbles(fr)
    x = [0.0] * LEAD
    f = symbol_carriers if mode == "whistle" else symbol_direct
    for k in nib:
        x += f(k, amp)
    return x, fr


def write_wav(samples, bits=24, full=0.95):
    peak = max(abs(s) for s in samples) or 1.0
    scale = (2 ** (bits - 1) - 1) * full / peak
    data = bytearray()
    lim = 1 << (bits - 1)
    for s in samples:
        v = int(round(s * scale))
        v = max(-lim, min(lim - 1, v))
        data += struct.pack("<i", v)[0:3]
    n = len(data)
    return (b"RIFF" + struct.pack("<I", 36 + n) + b"WAVE"
            + b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, MIC, MIC * 3, 3, 24)
            + b"data" + struct.pack("<I", n) + bytes(data))


def capture(payload, **kw):
    x, fr = build(payload, **kw)
    return write_wav(x), fr


if __name__ == "__main__":
    wav, fr = capture(bytes([0x10, 0x00]))
    print("frame:", fr.hex(), "bytes:", len(wav), "sec:", (len(wav) - 44) / 3 / MIC)
    open("ping_direct.bin", "wb").write(capture(bytes([0x10, 0x00]), mode="direct")[0])
    open("ping_whistle.bin", "wb").write(wav)
