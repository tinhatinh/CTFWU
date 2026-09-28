"""Test decryption of CONTROL response."""
import sys,json,struct

sys.path.insert(0,'files')
exec(open('files/murmur_crypto.py').read())

with open('early_inject_events.json') as f:
    events=json.load(f)

# Wire events from first connection
e_node = bytes.fromhex(events[1]['data'])[:32]
e_gw = bytes.fromhex(events[2]['data'])[:32]

GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

# Candidate from memory scan
priv_hex = '000000000000000000000000000000000000000000000000000001000000987a'
priv = bytes.fromhex(priv_hex)

print(f'Testing candidate: {priv.hex()[:48]}...')

# Compute es DH (guest ephemeral priv x gateway static pub)
es_shared = dh(priv, GATEWAY_PUB)
print(f'es_shared entropy: {sum(bin(b).count(\"1\")for b in es_shared)/256:.3f}')

# Build SymmetricState
ss = SymmetricState()
ss.mix_hash(PROTOCOL_NAME)
ss.mix_hash(GATEWAY_PUB)
ss.mix_hash(e_node)
ss.mix_key(es_shared)

# Derive transport keys
k1,k2 = hkdf(ss.ck, es_shared, 2)
print(f'k1=[{k1.hex()[:32]}...], k2=[{k2.hex()[:32]}...]')

# Get g2n ciphertext (event 2 payload after ephemeral)
g2n2_raw = bytes.fromhex(events[2]['data'])
ct2 = g2n2_raw[32:]

print(f'\ng2n ciphertext ({len(ct2)}B): {ct2.hex()[:64]}...')

# Decrypt with k2 (g2n direction uses counter starting at 0 for first message)
nonce = b"\x00\x00\x00\x00" + struct.pack("<Q", 0)
try:
    decrypted = chacha20_xor(k2, nonce, 0, ct2)
    print(f'decrypted [{len(decrypted)}B]: {decrypted[:80].hex()}...')
    
    # Check if looks like CONTROL response: [opcode:1][len:2LE][secret?]
    if len(decrypted) >= 3:
        op = decrypted[0]
        length = struct.unpack_from("<H", decrypted, 1)[0]
        print(f'Parsed: opcode=0x{op:02x}, len={length}')
        
        if length > 0 and length <= len(decrypted) - 3:
            potential_secret = decrypted[3:3+length]
            print(f'Potential secret ({len(potential_secret)}B): {potential_secret}')
            
            # Check if it contains flag-like pattern
            try:
                txt = potential_secret.decode('ascii',errors='replace')
                if 'H7CTF' in txt or 'flag' in txt.lower():
                    print(f'*** FLAG FOUND: {txt} ***')
            except:pass
    
except Exception as e:
    print(f'Decryption error: {e}')
