"""Client cho aria diagnostic bridge.

Mot dong = mot capture base64(WAV). Moi phan hoi ket thuc bang dong '----'.
Bank = 12 capture hop le / ket noi; ket noi lai moi duoc cap lai bank.
"""
import base64
import socket
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "pwn.h7tex.com"
PORT = 40918


class Aria:
    def __init__(self, host=HOST, port=PORT, timeout=25):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.buf = b""
        self.hello()

    def _read_until(self, marker=b"----", t=20.0):
        self.s.settimeout(t)
        while marker not in self.buf:
            try:
                c = self.s.recv(65536)
            except socket.timeout:
                break
            if not c:
                break
            self.buf += c
        i = self.buf.find(marker)
        if i < 0:
            out, self.buf = self.buf, b""
            return out
        i += len(marker)
        while i < len(self.buf) and self.buf[i - 1] not in b"\n":
            i += 1
        out, self.buf = self.buf[:i], self.buf[i:]
        return out

    def hello(self):
        return self._read_until(b"----", 3.0)

    def send_line(self, blob):
        self.s.sendall(base64.b64encode(blob) + b"\n")
        return self._read_until(b"----")

    def send_wavfile(self, path):
        with open(path, "rb") as f:
            return self.send_line(f.read())

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


if __name__ == "__main__":
    a = Aria()
    print("=== banner ===")
    print(a.hello().decode(errors="replace"))
    print("=== reference_ping.wav (hang goc) ===")
    print(a.send_wavfile("unpacked/reference_ping.wav").decode(errors="replace"))
    sys.path.insert(0, ".")
    import enc

    wav, fr = enc.make_capture(bytes([0x10, 0x00]))
    print("=== ping tu che, frame =", fr.hex(), "===")
    print(a.send_line(wav).decode(errors="replace"))
    a.close()
