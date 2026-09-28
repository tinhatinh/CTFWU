import struct
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import enc, client


def rec_select():
    return bytes([0x01, 0x01, 0x0E])


def rec_set(count, data):
    assert len(data) == 2 * count
    return bytes([0x02, 1 + 2 * count, count]) + data


def show(a, name, payload):
    wav, fr = enc.capture(payload)
    print("== %-24s %.2fs" % (name, (len(wav) - 44) / 3 / 96000))
    r = a.send_line(wav)
    print(repr(r)[:400])


# Gia dinh layout: g_cal = 32 byte dung duoc, chunk ke tiep la g_cal_desc
#   A+0x20 = prev_size (vo nghia), A+0x28 = size cua chunk desc (0x41), A+0x30 = desc.fn
SZ = struct.pack("<Q", 0x41)


def vec(n, hit=None):
    """n byte ghi tu dau g_cal, giu nguyen truong size cua chunk ke tiep."""
    d = bytearray(n)
    for i in range(8):
        if 40 + i < n:
            d[40 + i] = SZ[i]
    if hit:
        for i, b in enumerate(hit):
            if 48 + i < n:
                d[48 + i] = b
    return bytes(d)


a = client.Aria()
a.hello()
show(a, "select", rec_select())
show(a, "set 40B (vua het g_cal)", rec_set(20, vec(40)))
show(a, "select alive?", rec_select())
show(a, "set 42B size-preserved", rec_set(21, vec(42)))
show(a, "select alive2?", rec_select())
show(a, "set 50B desc.fn->26a0", rec_set(25, vec(50, hit=(0xA0, 0x26))))
a.close()
