#!/usr/bin/env python
"""my eyes burn -- recover the keystrokes that type the sun out of boardwriter.klc.

A .klc is a Windows keyboard-layout source (UTF-16LE). Two things matter here:

  * in the KEYS table a `@` on a character marks that key as a *dead key*
  * in a DEADKEY block, "<src> <res>@" means: while the dead-key state is the
    block's header, typing <src> leaves <res> as the new state; without the `@`
    the result is emitted as a real character and the chain ends.

Exactly one DEADKEY block terminates (02b0 + '}' -> U+2600 BLACK SUN WITH RAYS),
so walking the chain from the only dead key that is typed rather than produced
gives the unique keystroke sequence anon types.

usage: python solve_klc.py [boardwriter.klc]
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KLC = sys.argv[1] if len(sys.argv) > 1 else "files/boardwriter.klc"

text = open(KLC, "rb").read().decode("utf-16-le")

# --- dead keys that come straight off a physical key (KEYS table, `@` suffix) --
typed_dead = {}
for line in text.splitlines():
    f = line.split("\t")
    if len(f) == 6 and re.fullmatch(r"[0-9a-fA-F]{2}", f[0]):
        for col in (3, 4, 5):
            v = f[col]
            if v.endswith("@") and re.fullmatch(r"[0-9a-fA-F]{4}", v[:-1]):
                typed_dead[int(v[:-1], 16)] = f[1]

# --- DEADKEY blocks -----------------------------------------------------------
edges = {}          # state -> (source_char, result, result_is_dead)
state = None
for line in text.splitlines():
    s = line.strip()
    if s.startswith("DEADKEY"):
        state = int(s.split()[-1] if "\t" not in s else s.split("\t")[-1], 16)
    elif state is not None and re.fullmatch(r"[0-9a-fA-F]{4}\s+[0-9a-fA-F]{4}@?", s):
        src, res = s.split()
        dead = res.endswith("@")
        edges[state] = (int(src, 16), int(res[:-1] if dead else res, 16), dead)
    elif s.startswith("ENDKBD"):
        state = None

produced = {v[1] for v in edges.values() if v[2]}
entry = [k for k in edges if k not in produced and k in typed_dead]
terminals = [(k, v) for k, v in edges.items() if not v[2]]
print("[*] %d DEADKEY blocks, %d typed dead keys" % (len(edges), len(typed_dead)))
print("[*] chain entry points: %s" % [("%04X (%s)" % (k, typed_dead[k])) for k in entry])
print("[*] terminals (non-dead output): %s"
      % ["%04X + %s -> %s U+%04X" % (k, chr(v[0]), chr(v[1]), v[1]) for k, v in terminals])

keys, state_cur, hops = [], entry[0], None
walk = entry[0]
seq = []
while True:
    src, res, dead = edges[walk]
    seq.append((walk, src, res, dead))
    keys.append(chr(src))
    if not dead:
        final = res
        break
    walk = res
    if len(seq) > 60:
        sys.exit("[-] cycle")

print("\n[*] walk (state, key pressed, next state):")
for st, src, res, dead in seq:
    print("    %04X  +  %-3s ->  %04X %s" % (st, chr(src), res, "(dead)" if dead else "(EMITTED)"))

typed = chr(entry[0]) + "".join(keys)
print("\n[*] keystrokes: %r" % typed)
print("[*] emits: %s  (U+%04X %s)" % (final, final, "BLACK SUN WITH RAYS"))
# the leading backtick is only the dead-key trigger; what appears on screen is the rest
flag = "".join(keys)
print("[+] FLAG: %s" % flag)
open("flag.txt", "w", encoding="utf-8").write(flag)
