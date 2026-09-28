"""Efficient scan of 17GB memory.raw for X25519 private scalars."""
import os, sys, hashlib

fname = 'files/memory.raw'
sz = os.path.getsize(fname)
print(f'Scanning {fname} ({sz/(1024**3):.2f} GB)...')

# X25519 private key format (little-endian):
# - Bits 0-2 cleared: scalar % 8 == 0
# - Bit 254 set (bit index from LSB): (scalar >> 254) & 1 == 1
# - Bit 255 cleared: not negative
def is_valid_x25519_scalar_le(b):
    if len(b) != 32:
        return False
    v = int.from_bytes(b, 'little')
    return ((v & 7) == 0) and ((v >> 254) & 1) and not((v >> 255) & 1)

found = []
batch_size = 0x100000  # 1MB chunks
with open(fname, 'rb') as f:
    offset = 0
    while True:
        chunk = f.read(batch_size)
        if not chunk:
            break
        
        # Scan window over chunk
        for i in range(len(chunk) - 31):
            candidate = chunk[i:i+32]
            if is_valid_x25519_scalar_le(candidate):
                found.append((offset + i, candidate.hex()))
                if len(found) >= 50:
                    print(f'Found {len(found)} candidates, stopping...')
                    break
        else:
            offset += batch_size
            continue
        break
    
    if not found:
        print('No valid X25519 scalars found!')
        sys.exit(0)

print(f'\nTotal candidates: {len(found)}')
for off, hx in found[:20]:
    print(f'  @0x{off:08x}: {hx}')

# Now try to use each candidate to decrypt the CONTROL response
print('\n\nAttempting decryption with each candidate as guest ephemeral private key...')
sys.path.insert(0, '.')
exec(open('murmur_crypto.py').read())

GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

# From tap events, we have:
eph_node_pub_hex = 'a8ad536a5d171b74a1835b30ac1b4ea820c1abfaa3b8f1a4075a0c690ec7a47'
g2n_frame_hex = '17fc194b3fc4e8011e434ec11a3cb349108889faa4909abf7bdce9ba82724571097882b6f10d41880716a9322f19eae1'

eph_node_pub = bytes.fromhex(eph_node_pub_hex)
g2n_frame = bytes.fromhex(g2n_frame_hex)

print(f'Target g2n frame: {len(g2n_frame)}B, ciphertext={len(g2n_frame)-16}B, tag={16}B')

best_score = None
best_candidate = None

for off, priv_le_hex in found:
    try:
        priv = bytes.fromhex(priv_le_hex)
        # Compute DH: shared_secret = X25519(private, other_public)
        shared = dh(priv, GATEWAY_PUB)
        
        # If this is correct, shared should look like valid X25519 output (32 random-looking bytes)
        # We can't verify without session key, but we can check entropy
        entropy = sum(bin(b).count('1') for b in shared) / (32 * 8)
        
        # Also derive session key via SymmetricState
        ss = SymmetricState()
        ss.mix_hash(crypto.PROTOCOL_NAME)
        ss.mix_hash(GATEWAY_PUB)
        ss.mix_hash(bytes.fromhex(eph_node_pub_hex))
        ss.mix_key(shared)  # es DH
        
        # Continue handshake simulation...
        # This is getting complex, let's just score by entropy for now
        if best_score is None or entropy > best_score:
            best_score = entropy
            best_candidate = (off, priv_le_hex, entropy)
            
    except Exception as e:
        pass

if best_candidate:
    print(f'\nBest candidate by entropy: @0x{best_candidate[0]:08x}, entropy={best_candidate[2]:.3f}')
    print(f'Suggested private key: {best_candidate[1]}')
else:
    print('\nNo candidates scored well')
