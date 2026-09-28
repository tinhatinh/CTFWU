"""Backward solver for guardian programs: recover the key bytes a shard accepts.

`know` maps a cell number to the value it MUST hold at the current (moving-backwards)
program point.  A KEY instruction turns that value into a constraint on key[idx].
ANDI/OR/AND leave free bits; those are returned so the caller can enumerate them and
verify every candidate with the real emulator (vm.VM).
"""
import os, sys, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vm

M32 = 0xFFFFFFFF


def inv_perm(p):
    q = [0] * 256
    for i, v in enumerate(p):
        q[v] = i
    return q


def decode(sh, seq):
    out = []
    for pc, op in seq:
        if vm.W[op] == 1:
            out.append((pc, op, None, None, None))
        elif vm.W[op] == 3:
            out.append((pc, op, sh['code'][pc + 1], sh['code'][pc + 2], None))
        else:
            out.append((pc, op, sh['code'][pc + 1], None,
                        struct.unpack_from('<I', sh['code'], pc + 2)[0]))
    return out


def backwards(sh, seq, table=None):
    tbl = table if table is not None else (list(range(256)), sh['tbl'])
    inv_s = inv_perm(sh['sbox'])
    ins = decode(sh, seq)
    know = {}
    keyreq = {}
    free = []
    pend = list(reversed(ins))
    for _round in range(2000):
        nxt = []
        moved = False
        for it in pend:
            pc, op, a, b, imm = it
            if op == 0:
                moved = True
                continue
            if op == 11:                                   # CMP rA, imm
                if a in know and know[a] != imm:
                    raise ValueError('CMP contradiction r%d=%08x want %08x' % (a, know[a], imm))
                if a not in know:
                    know[a] = imm
                moved = True
                continue
            if a is None or a not in know:
                nxt.append(it)
                continue
            p = know[a]
            done = True
            if op == 1:                                    # KEY rA, idx
                if p > 0xFF:
                    raise ValueError('KEY cell not a byte')
                keyreq[b] = p
                know.pop(a)
            elif op == 2:                                  # MOVI rA, imm
                if p != imm:
                    raise ValueError('MOVI contradiction')
                know.pop(a)
            elif op == 3:                                  # MOV rA, rB
                if a == b:                                 # no-op
                    moved = True
                    continue
                know.pop(a)
                if b in know and know[b] != p:
                    raise ValueError('MOV contradiction')
                know[b] = p
            elif op == 10:                                 # LUT rA, rB
                if p > 0xFF:
                    raise ValueError('LUT cell not a byte')
                v = inv_s[p]
                know.pop(a)
                if b != a:
                    if b in know and know[b] != v:
                        raise ValueError('LUT contradiction')
                    know[b] = v
                else:
                    know[a] = v
            elif op == 4:                                  # XOR rA, rB
                if a == b:                                 # rA = 0; pre-value unconstrained
                    if p:
                        raise ValueError('self-XOR leaves nonzero')
                    know.pop(a)
                elif b in know:
                    know[a] = p ^ know[b]
                else:
                    done = False
            elif op == 13:                                 # XORI rA, imm
                know[a] = p ^ imm
            elif op == 5:                                  # ADD rA, rB
                if b in know:
                    know[a] = (p - know[b]) & M32
                elif b == a:
                    done = False
                else:
                    done = False
            elif op == 9:                                  # ROL rA, imm8
                n = (b if b is not None else 0) & 31
                know[a] = vm.rol32(p, (-n) & 31)
            elif op == 12:                                 # ANDI rA, imm
                for i in range(8):                         # only the low byte can vary
                    if not (imm >> i) & 1:
                        free.append((a, i))
                know[a] = p
            elif op == 7:                                  # AND rA, rB
                if b in know:
                    r = know[b]
                    if p & ~r:
                        raise ValueError('AND impossible')
                    for i in range(32):
                        if not (r >> i) & 1:
                            free.append((a, i))
                    know[a] = p
                else:
                    done = False
            elif op == 8:                                  # OR rA, rB
                if b in know:
                    r = know[b]
                    for i in range(32):
                        if (r >> i) & 1:
                            free.append((a, i))
                    know[a] = p & ~r if (p & r) == r else p
                    if (p | r) != p and (p & r) != r:
                        raise ValueError('OR impossible')
                else:
                    done = False
            elif op == 6:                                  # MUL rA, rB
                if b in know and know[b] % 2 == 1:
                    know[a] = (p * pow(know[b], -1, 1 << 32)) & M32
                else:
                    done = False
            if not done:
                nxt.append(it)
            else:
                moved = True
        pend = nxt
        if not moved:
            break
    return know, keyreq, free, pend


def candidates(shname, table=None, verbose=False):
    sh = vm.load(shname)
    if table is not None:
        sh['tbl'] = list(table)
    seq, st, ex = vm.dismap(sh)
    if st == 'BADOP':
        return None, 'badop'
    know, keyreq, free, pend = backwards(sh, seq, table)
    if pend or not keyreq:
        return {'know': know, 'keyreq': keyreq, 'free': free, 'pend': pend}, 'stuck'
    base = bytes(keyreq.get(i, 0) for i in range(8))
    bits = {}
    for reg, i in free:
        bits.setdefault(min(reg, 7), set()).add(i)
    spots = sorted(bits)
    sets = [sorted(bits[s]) for s in spots]
    n = sum(len(x) for x in sets)
    out = []
    for mask in range(1 << n):
        k = bytearray(base)
        m = mask
        for si, s in enumerate(spots):
            for b in sets[si]:
                bit = m & 1
                m >>= 1
                if bit:
                    k[s] |= 1 << b
        cand = bytes(k)
        v = vm.VM(sh['tbl'], sh['sbox'], sh['code'], cand)
        if v.run() == ('HALT', len(sh['code']) - 1) or v.run()[0] == 'HALT':
            out.append(cand)
        if len(out) > 5000:
            break
    return {'keyreq': keyreq, 'free': free, 'n': n}, out


if __name__ == '__main__':
    for n in (sys.argv[1:] or ['f6f11ad133cab21c96e0185e3411ddc4']):
        info, out = candidates(n)
        print('####', n[:12])
        if info is None:
            print('   table unreadable'); continue
        print('   keyreq:', {k: hex(v) for k, v in sorted(info.get('keyreq', {}).items())},
              ' freebits:', info.get('free'), ' pend:', len(info.get('pend', [])))
        if isinstance(out, list):
            print('   accepting keys: %d' % len(out))
            for c in out[:6]:
                print('     ', c.hex())
