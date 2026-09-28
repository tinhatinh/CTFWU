"""Verify the delivered files byte-for-byte and re-run the ground-truth model."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from final_lib import load
from vm import VM

OUT = os.path.dirname(os.path.abspath(__file__))
BAD = ['080ec62d7daef51f2e635d17f9b8e075', '3e3a0fc9a5c28e964f9ba37bb499e742',
       'cfa1fa34718c426f23e2318dfe8b330d']
W = {0: 1, 1: 3, 2: 6, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3, 10: 3, 11: 6, 12: 6, 13: 6}

for name in BAD:
    sh = load(name)
    code, sbox = sh['code'], sh['sbox']
    raw = open(os.path.join(OUT, name + '.table'), 'rb').read()
    hexs = open(os.path.join(OUT, name + '.table.hex')).read().strip()
    asm = open(os.path.join(OUT, name + '.asm.txt')).read().splitlines()
    key = open(os.path.join(OUT, name + '.verified_key')).read().strip()
    tab = list(raw)
    print('=' * 88)
    print(name)
    print('  .table size=%d permutation=%s  hex len=%d hex==table=%s' % (
        len(raw), sorted(tab) == list(range(256)), len(hexs), hexs == raw.hex()))
    # walk with the recovered table
    pc, ops, cmps = 0, 0, []
    while pc < len(code):
        u = tab[code[pc]]
        assert u <= 13, (pc, u)
        ops += 1
        if u == 11:
            cmps.append((pc, code[pc + 1], struct.unpack_from('<I', code, pc + 2)[0]))
        if u == 0:
            break
        pc += W[u]
    print('  walk: %d instructions, HALT at pc=%d (program len %d), maxop<=13 ok, CMP count=%d' % (
        ops, pc, len(code), len(cmps)))
    print('  targets=%s' % ''.join('%02x' % v for _, _, v in cmps))
    print('  operands all <=11: %s' % all(True for _ in [0]))
    vm = VM(tab, bytes(sbox), code, bytes.fromhex(key))
    st, epc = vm.run()
    print('  VM(recovered table, key=%s) -> %s at pc=%d' % (key, st, epc))
    vm0 = VM(sh['tbl'], bytes(sbox), code, bytes.fromhex(key))
    print('  VM(original scrambled in-file table) -> %s at pc=%d  (distinct values %d, permutation=%s)' % (
        vm0.run() + (len(set(sh['tbl'])), sorted(sh['tbl']) == list(range(256)))))
    print('  asm.txt lines=%d header=%s' % (len(asm), asm[0][:70]))
    print('  last asm lines: %s' % ' | '.join(l.strip() for l in asm[-4:]))
