import sys,json,struct

sys.path.insert(0,'files')
exec(open('files/murmur_crypto.py').read())

with open('tap_full.json') as f:
    events=json.load(f)

# Events
# 1: n2g 48B -> msg1 e_node+ct1
# 2: g2n 48B -> msg2 e_gw+ct2  
# 3: n2g 64B -> msg3 encrypted_s_guest
# 5: g2n 662B -> gateway response (TELEMETRY reply?)

events_map = {i:e for i,e in enumerate(events)}
n2g_msg1 = bytes.fromhex(events_map[1]['data'])
g2n_msg2 = bytes.fromhex(events_map[2]['data'])
g2n_response = bytes.fromhex(events_map[5]['data'])

e_node = n2g_msg1[:32]
e_gw = g2n_msg2[:32]

print('e_node:', e_node.hex()[:32], '...')
print('e_gw:', e_gw.hex()[:32], '...')
print('\ng2n_response len:', len(g2n_response), 'bytes')
print('First 64B:', g2n_response[:64].hex(), '...')

GATEWAY_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')

# Try all 50 candidates
candidates=[
'000000000000000000000000000000000000000000000000000001000000987a',
'0000000000000000000000000000000000000000000001000000987a0f00f360',
'000000000000000000000001000000987a0f00f3600f00010000000000000042',
'0000000000000000000001000000987a0f00f3600f0001000000000000004273',
'0000000000000000000000000000d4ff0500e0e30e0002760f00565c0f00d46f',
'00000000000000000000000000000000f004005e01050000f004000030050050',
'00009c7a0f000401000094afa4be000000000001000000000000bc5b0f00d46f',
'00000000000000000000000000000000000000000000d4ff0500e0e30e000276',
'00000000000000000000000000000000000000d4ff0500e0e30e0002760f0056',
'0000000000000000000001000000987a0f00f3600f0001000000000000004273',
'000000000000000000000001000000987a0f00f3600f00010000000000000042',
]

print('\nTrying candidates against g2n_response...')
for priv_hex in candidates:
    try:
        priv=bytes.fromhex(priv_hex)
        
        # es DH
        es_shared=dh(priv,GATEWAY_PUB)
        
        ss=SymmetricState()
        ss.mix_hash(PROTOCOL_NAME)
        ss.mix_hash(GATEWAY_PUB)
        ss.mix_hash(e_node)
        ss.mix_key(es_shared)
        
        k1,k2=hkdf(ss.ck,es_shared,2)
        
        # Try decrypting g2n_response with k2
        # But response might be multiple frames concatenated!
        # Let's just try first frame assuming it starts with [type:1][AEAD]
        
        # Actually g2n_response size 662B is too big for single CONTROL response
        # Could be TELEMETRY reply which is also encrypted
        
        # Let's try AEAD decrypt anyway
        nonce=b'\x00'*4+struct.pack('<Q',0)
        try:
            decrypted=chacha20_xor(k2,nonce,0,g2n_response[:-16])
            tag=g2n_response[-16:]
            
            # Check if poly1305 tag matches
            poly_key=chacha20_block(k2,0,nonce)[:32]
            # ...poly1305 check omitted for speed
            
            # Check if decrypted has flag pattern
            hex_str=decrypted.hex()
            if 'h7ctf{' in hex_str.lower() or 'flag{' in hex_str.lower():
                print(f'*** FLAG FOUND with {priv_hex[:48]}... ***')
                print(hex_str[:200])
                
        except Exception as ex:
            pass
    
    except Exception as ex:
        pass

print('Done testing')
