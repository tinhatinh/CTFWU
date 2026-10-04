import numpy as np
from solve import build, P

CT = "XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`"
N = len(CT)
kvec, avec, BET = build(N)
Y = [ord(c) - 60 for c in CT]

def eqs(known):
    rows, rhs = [], []
    for i, ch in known.items():
        x = ord(ch) - 60
        rows.append([int(v) % P for v in BET[i]])
        rhs.append((int(kvec[i]) * x - Y[i] - int(avec[i])) % P)
    return np.array(rows), np.array(rhs)

prefix = {i: c for i, c in enumerate('cdctf{')}
R6, H6 = eqs(prefix)
R7, H7 = eqs(prefix | {N - 1: '}'})

cands = []
for w in open('words_alpha.txt', encoding='utf-8', errors='ignore'):
    w = w.strip()
    if len(w) == 11:
        cands += [w, w.capitalize(), w.upper()]
cands += ['birthdayboy', 'b1rthdayb0y', 'h4ppybirthday'[:11], 'feistelfun', 'REALCRYPTO!',
          'gl2-88-hs!!', 'nottoomathh', 'symmetricxx', 'streamcipherr'[:11], 'reep236reep',
          '3dgehogfhgfd', 'prettypr0duct'[:11], 'birthdaycake'[:11], 'happyb1rthd4y',
          'h4ppybday!!', 'mathnotreal', 'notmathjust', 'realcrypto1']
LEET = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
extra = []
for w in [c for c in cands if c.isalpha()][:40000]:
    for pos, ch in enumerate(w):
        if ch in LEET:
            v = w[:pos] + LEET[ch] + w[pos + 1:]
            if len(v) == 11:
                extra.append(v)
cands += extra
uniq = sorted({c for c in cands if len(c) == 11 and all(32 <= ord(x) < 127 for x in c)})
print('candidate keys:', len(uniq))

def mydec(kvv):
    aa = [(int(avec[i]) + int(BET[i] @ np.array(kvv, dtype=object))) % P for i in range(N)]
    return ''.join(chr((pow(int(kvec[i]), P - 2, P) * ((ord(c) - 60) + aa[i])) % P + 60)
                   for i, c in enumerate(CT))


C = np.array([[(ord(x) - 60) % P for x in k] for k in uniq], dtype=np.int64)
ok6 = ((C @ R6.T) % P == H6).all(axis=1)
ok7 = ((C @ R7.T) % P == H7).all(axis=1)
print('pass 6 prefix eqs:', int(ok6.sum()), '| pass all 7:', int(ok7.sum()))
for tag, mask in (('6eq', ok6), ('7eq', ok7)):
    for name in list(np.array(uniq)[mask]):
        print(tag, repr(name), '->', mydec([(ord(x) - 60) % P for x in name]))
