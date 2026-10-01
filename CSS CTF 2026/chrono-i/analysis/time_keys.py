"""Thu sinh key stream tu chuoi thoi gian 2026-09-21 14:35:07.

Crib: plaintext "CSSCTF" -> ciphertext "ESUITO".
Voi moi key stream thu, kiem ca ba kieu: Vigenere (c=p+k), Beaufort (c=k-p),
variant (c=p-k).
"""

import datetime as dt
import itertools
import re

P = [ord(c) - 97 for c in "cssctf"]
C = [ord(c) - 97 for c in "esuito"]
NEED = [(c - p) % 26 for p, c in zip(P, C)]
NEED_B = [(c + p) % 26 for p, c in zip(P, C)]      # Beaufort: k = c + p
NEED_V = [(p - c) % 26 for p, c in zip(P, C)]      # variant : k = p - c

TS = dt.datetime(2026, 9, 21, 14, 35, 7)
SOURCES = {}


def digits(n):
    return [int(x) for x in re.sub(r"\D", "", str(n))]


def base26(n, msb=True):
    out = []
    n = abs(int(n))
    if n == 0:
        return [0]
    while n:
        out.append(n % 26)
        n //= 26
    return out[::-1] if msb else out


def add(name, seq):
    seq = [x % 26 for x in seq]
    if seq:
        SOURCES[name] = seq


def variants(tag, num, digits_):
    add(tag + ".digits", digits_)
    add(tag + ".cumsum", list(itertools.accumulate(digits_)))
    add(tag + ".idx", [d * (i + 1) for i, d in enumerate(digits_)])
    add(tag + ".idx2", [d + i for i, d in enumerate(digits_)])
    add(tag + ".pairs", [int(digits_[i]) * 10 + digits_[i + 1] for i in range(0, len(digits_) - 1, 2)])
    add(tag + ".base26msb", base26(num, True))
    add(tag + ".base26lsb", base26(num, False))
    add(tag + ".hex", [int(x, 16) for x in "%x" % abs(int(num))])


epoch_utc = int(TS.replace(tzinfo=dt.timezone.utc).timestamp())
for off, tag in ((0, "utc"), (7, "utc7"), (10, "aest"), (-4, "edt")):
    e = epoch_utc - off * 3600
    variants("epoch" + tag, e, digits(e))

forms = {
    "compact": "20260921143507",
    "dmy": "21092026143507",
    "date": "20260921",
    "time": "143507",
    "ymd_dash": "2026-09-21",
    "sec_of_day": TS.hour * 3600 + TS.minute * 60 + TS.second,
    "doy": TS.timetuple().tm_yday,
}
for k, v in forms.items():
    n = int(re.sub(r"\D", "", str(v)))
    variants(k, n, digits(v))

fields = [TS.year, TS.month, TS.day, TS.hour, TS.minute, TS.second]
add("fields", fields)
add("fields.cumsum", list(itertools.accumulate(fields)))
add("fields.digits", [d for f in fields for d in digits(f)])
add("fields.digits.cumsum", list(itertools.accumulate([d for f in fields for d in digits(f)])))
add("fields.x2", [x * 2 for x in fields])
add("fields.rev", fields[::-1])
add("fields.rev.cumsum", list(itertools.accumulate(fields[::-1])))

print("crib Vigenere  :", NEED)
print("crib Beaufort  :", NEED_B)
print("crib variant   :", NEED_V)
print("nguồn đã thử   :", len(SOURCES))
hits = 0
for name, seq in sorted(SOURCES.items()):
    for kind, need in (("vig", NEED), ("bea", NEED_B), ("var", NEED_V)):
        ok = all(seq[i % len(seq)] == need[i] for i in range(len(need)))
        if len(seq) >= len(need) and ok:
            print("KHOP %s %s -> %s" % (kind, name, seq))
            hits += 1
print("so khop:", hits)
