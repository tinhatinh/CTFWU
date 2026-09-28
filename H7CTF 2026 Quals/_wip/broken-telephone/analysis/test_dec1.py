import sys,json,struct

sys.path.insert(0,'files')
exec(open('files/murmur_crypto.py').read())

with open('early_inject_events.json') as f:
    events=json.load(f)

e_node = bytes.fromhex(events[1]['data'])[:32]
GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

priv_hex = '000000000000000000000000000000000000000000000000000001000000987a'
priv = bytes.fromhex(priv_hex)

print('Testing candidate:', priv_hex[:48])

es_shared = dh(priv, GATEWAY_PUB)
entropy = sum(bin(b).count('1') for b in es_shared) / 256
print('es_shared entropy:', entropy)

ss = SymmetricState()
ss.mix_hash(PROTOCOL_NAME)
ss.mix_hash(GATEWAY_PUB)
ss.mix_hash(e_node)
ss.mix_key(es_shared)

k1,k2 = hkdf(ss.ck, es_shared, 2)
print('k1:', k1.hex()[:32], '...')
print('k2:', k2.hex()[:32], '...')

g2n2_raw = bytes.fromhex(events[2]['data'])
ct2 = g2n2_raw[32:]
print('g2n ciphertext len:', len(ct2))

nonce = b"\x00\x00\x00\x00" + struct.pack('<Q', 0)
decrypted = chacha20_xor(k2, nonce, 0, ct2)
print('Decrypted:', decrypted[:80].hex(), '...')

if len(decrypted) >= 3:
    op = decrypted[0]
    length = struct.unpack_from('<H', decrypted, 1)[0]
    print('opcode:', hex(op), 'len:', length)
    
    if length > 0 and length <= len(decrypted) - 3:
        secret = decrypted[3:3+length]
        print('Potential secret:', secret)
        try:
            txt = secret.decode('ascii', errors='replace')
            if 'H7CTF' in txt or 'flag{' in txt.lower():
                print('FLAG FOUND:', txt)
        except:pass
