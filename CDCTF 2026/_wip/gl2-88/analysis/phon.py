import numpy as np

CT = "XwFAN`aXUspHB~]bhjV>_Fmk}VJ~tx=BwsvP<hK[XOo`"
lam = np.load('soft_lam.npy'); rows = np.load('soft_rows.npy'); cnt = np.load('soft_cnt.npy')
VOW = set('aeiouyAEIOUY')
SEP = set('_')


def maxrun(s, pred):
    best = cur = 0
    for c in s:
        if pred(c):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


out = []
for n in range(len(rows)):
    body = ''.join(chr(int(v) + 60) for v in rows[n])
    letters = ''.join(c for c in body if c.isalpha())
    if len(letters) < 33:
        continue
    if maxrun(body, lambda c: c.isalpha() and c not in VOW) > 3:
        continue
    if maxrun(body, lambda c: c in VOW and c not in 'yY') > 3:
        continue
    if any(a == b for a, b in zip(body, body[1:]) if a.isalpha()):
        continue
    if 'q' in body.lower() and 'u' not in body.lower():
        continue
    if body.lower().count('j') + body.lower().count('k') + body.lower().count('z') > 2:
        continue
    rare = sum(body.lower().count(c) for c in 'qxzjk')
    vowels = sum(1 for c in body if c in VOW)
    flag = 'cdctf{' + body + '}'
    out.append((rare, -vowels, vowels / max(1, len(letters)), flag, int(lam[n])))
out.sort()
print('phonotactic survivors:', len(out))
with open('phon.txt', 'w') as f:
    for r in out:
        f.write(r[3] + '\t' + str(r[4]) + '\n')
for r in out[:60]:
    print(r[0], r[2], r[3])
