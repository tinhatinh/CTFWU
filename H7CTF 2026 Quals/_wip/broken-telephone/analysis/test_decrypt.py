"""Broken Telephone - test decrypted CONTROL response."""
import sys,json,struct
sys.path.insert(0,'files')
exec(open('files/murmur_crypto.py').read())

with open('early_inject_events.json') as f:
    events=json.load(f)

e_node = bytes.fromhex(events[1]['data'])[:32]
g2n1 = bytes.fromhex(events[2]['data'])
e_gw = g2n1[:32]
ct1 = g2n1[32:]
ct2 = g2n1[32:]  # placeholder

GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

# Try candidate
priv_hex = '000000000000000000000000000000000000000000000000000001000000987a'
priv = bytes.fromhex(priv_hex)

print(f'Testing candidate: {priv.hex()[:48]}...')

# Step 1: Compute es DH (guest ephemeral priv x gateway static pub)
es_shared = dh(priv, GATEWAY_PUB)
print(f'es_shared: {es_shared.hex()[:64]}... entropy={sum(bin(b).count(\"1\")for b in es_shared)/256:.3f}')

# Build SymmetricState for initiator side
ss = SymmetricState()
ss.mix_hash(PROTOCOL_NAME)
ss.mix_hash(GATEWAY_PUB)
ss.mix_hash(e_node)
ss.mix_key(es_shared)

# Read msg1 (we have it from tap already as e_node+ct1)
# ct1 should decrypt to payload + authentication tag
try:
    # After mixing_hash(e_node), the state has ck derived from protocol+gateway_pub+eph
    # But we still need es DH output for key derivation...
    # Actually according to code, mix_key(es) comes AFTER mix_hash(e) in write_msg1
    # Let's follow exact sequence
    
    # The ciphertext ct1 was encrypted after ss.encrypt_and_hash(payload) which does:
    #   seal = AEAD(key, nonce, plaintext+tag, h_state_before_encrypt)
    # where key comes from hkdf(ck, es_DH_output, 2)
    
    # So we need to derive transport keys first
    k1,k2 = hkdf(ss.ck, es_shared, 2)  # k1 for n2g, k2 for g2n
    
    print(f'transport_keys derived: k1={k1.hex()[:32]}... k2={k2.hex()[:32]}...')
    
except Exception as ex:
    print(f'Key derivation error: {ex}')
    sys.exit(1)

# Now try to decrypt the g2n frame
# First wire event structure: [ephemeral_pub:32][encrypted_payload]
# We need to parse message 3 (n2g 64B) to get s_guest_pub

msg3_hex = events[3]['data']  # Should be encrypted(s_guest) + encrypted(telemetry)
msg3_raw = bytes.fromhex(msg3_hex)
print(f'\nmsg3 ({len(msg3_raw)}B): {msg3_raw[:48].hex()}...')

# According to write_msg3: buf = ss.encrypt_and_hash(self.s_pub) + ss.encrypt_and_hash(payload)
# Each part gets 16B AEAD tag, so:
#   encrypted_static = s_guest_pub (32B) + tag (16B) = 48B
#   encrypted_telemetry = telemetry (64B?) + tag (16B) = 80B? 

# Total msg3 size varies, let's just see what we have
if len(msg3_raw) >= 48:
    enc_static = msg3_raw[:48]
    tag_enc_static = enc_static[-16:]
    cipher_static = enc_static[:-16]
    
    print(f'enc_static_cipher ({len(cipher_static)}B): {cipher_static.hex()}')
    print(f'enc_static_tag: {tag_enc_static.hex()}')
    
    # Decrypt with transport key k1 (n2g direction, but this is s_pub from guest to gateway = n2g)
    try:
        nonce = b"\x00\x00\x00\x00" + struct.pack("<Q", 0)  # First message in stream
        decrypted_static = chacha20_xor(k1, nonce, 0, cipher_static)
        
        # Check if result looks like valid X25519 public key (just check high entropy)
        entropy = sum(bin(b).count("1") for b in decrypted_static) / 256
        print(f'decrypted_static: {decrypted_static.hex()[:64]}... entropy={entropy:.3f}')
        
        if entropy > 0.45:
            print(f'*** Looks like valid X25519 public key! ***')
            
    except Exception as dec_ex:
        print(f'Decrypt error: {dec_ex}')
