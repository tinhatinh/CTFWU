import sys,json,struct

sys.path.insert(0,'files')
exec(open('files/murmur_crypto.py').read())

with open('tap_full.json') as f:
    events=json.load(f)

# msg3 = event 3: n2g 64B
msg3_raw = bytes.fromhex(events[3]['data'])
print('msg3 len:',len(msg3_raw),'B')
print('First 80B:',msg3_raw[:80].hex(),'...')

# According to write_msg3: buf = ss.encrypt_and_hash(self.s_pub) + ss.encrypt_and_hash(payload)
# s_pub should be X25519 public key (32B) + AEAD tag (16B) = 48B encrypted_static
# Then telemetry payload encrypted separately

GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

# Candidates (top entropy ones from memory scan)
candidates=[
'00009c7a0f000401000094afa4be000000000001000000000000bc5b0f00d46f',
'0000ffffffff00000000a4aea4be000000000001000000000000bc5b0f00d46f',
]

for priv_hex in candidates:
    priv=bytes.fromhex(priv_hex)
    
    # es DH
    es_shared=dh(priv,GATEWAY_PUB)
    print('\nTesting',priv_hex[:40],'...')
    print('es_shared first 32B:',es_shared[:32].hex(),'entropy=',sum(bin(b).count('1')for b in es_shared)/256)
    
    # Build SS
    ss=SymmetricState()
    ss.mix_hash(PROTOCOL_NAME)
    ss.mix_hash(GATEWAY_PUB)
    
    e_node=bytes.fromhex(events[1]['data'])[:32]
    ss.mix_hash(e_node)
    ss.mix_key(es_shared)
    
    k1,k2=hkdf(ss.ck,es_shared,2)
    print('k1:',k1.hex()[:32],'...')
    
    # Decrypt encrypted_static (first 48B of msg3)
    enc_static=msg3_raw[:48]
    cipher_static=enc_static[:-16]
    nonce=b'\x00'*4+struct.pack('<Q',0)
    
    try:
        decrypted_s_pub=chacha20_xor(k1,nonce,0,cipher_static)
        print('Decrypted s_pub candidate:',decrypted_s_pub.hex()[:64],'...')
        
        # Check if looks like valid X25519 pub (high entropy)
        entropy=sum(bin(b).count('1')for b in decrypted_s_pub)/256
        if entropy>0.45:
            print('*** VALID X25519 PUBLIC KEY CANDIDATE ***')
            print('Entropy:',entropy)
            
    except Exception as ex:
        print('Decrypt error:',ex)
