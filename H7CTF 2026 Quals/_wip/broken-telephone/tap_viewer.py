"""Broken Telephone - quick tap viewer and transcript analyzer."""
import os, sys, json, socket, struct, asyncio

here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)

# Load murmur_crypto inline
script_path = os.path.join(murmur_dir, 'murmur_crypto.py')
with open(script_path) as f:
    code = f.read()
ns = {}
exec(code, ns)
crypto = type(sys)('murmur_crypto')
crypto.__dict__.update(ns)

GATEWAY_STATIC_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')


async def capture_and_analyze(port, timeout=10):
    """Capture all wire events, parse handshake, try to compute h2."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection error: {ex}')
        return None
    
    wire_events = []
    buffer = b''
    
    print('[*] Capturing tap traffic...')
    while True:
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
            lines = buffer.split(b'\n')
            buffer = lines[-1]
            
            for line in lines[:-1]:
                if not line.strip():
                    continue
                obj = json.loads(line.decode('utf-8'))
                evt = obj.get('event')
                if evt == 'wire':
                    direction = obj.get('dir')
                    data_hex = obj.get('data')
                    raw = bytes.fromhex(data_hex)
                    wire_events.append((direction, raw))
                    print(f'[wire] {direction}: {len(raw)}B -> {raw.hex()}')
                elif evt == 'session':
                    print(f'[session] proto={obj.get("proto")}')
                elif evt == 'ready':
                    print('[tap ready, waiting for more events...]')
                    
        except Exception as ex:
            print(f'Recv error: {ex}')
            break
    
    sock.close()
    print(f'\n[*] Total {len(wire_events)} wire events captured')
    
    if len(wire_events) < 3:
        print('[!] Not enough events for full handshake')
        return None
    
    # Try to reconstruct transcript according to Noise XKpsk3
    # For initiator: msg1=e+encrypted(es+payload), msg2=e+encrypted(ee+payload), msg3=encrypted(s_pub)+encrypted(payload)
    
    n2g_msgs = [raw for d, raw in wire_events if d == 'n2g']
    g2n_msgs = [raw for d, raw in wire_events if d == 'g2n']
    
    print(f'[!] n2g msgs ({len(n2g_msgs)}): {[len(x) for x in n2g_msgs]}B')
    print(f'[!] g2n msgs ({len(g2n_msgs)}): {[len(x) for x in g2n_msgs]}B')
    
    # Hypothesis: each message is just 16B encrypted (after mixing_hash(pub)), not including ephemeral key
    # Let's check if we can decrypt assuming this
    
    # Alternative approach: maybe the ephemeral keys are NOT prepended; they're separate events or implicit
    # Check if any event contains a 32B hex string that looks like X25519 pub
    
    print('\n[*] Looking for X25519 public keys (32B high entropy)...')
    for i, (direction, raw) in enumerate(wire_events):
        if len(raw) >= 32:
            # Quick entropy check: number of set bits
            bits = sum(bin(b).count('1') for b in raw[:32])
            if bits > 100:  # reasonable threshold for random 32B
                print(f'  Event {i} ({direction}, {len(raw)}B): high entropy start -> {raw[:32].hex()}')
    
    # Now let's try to compute h2 ourselves from what we know
    # According to spec, transcript includes: protocol name, gateway static pubkey, both ephemeral pubs, two ciphertexts
    # But we don't see ephemeral pubs explicitly in the wire events (only 48B per event)
    
    # Maybe ephemeral key IS embedded in the first part of message?
    # msg1[0:32]=e_node, msg1[32:48]=ct1 => only 16B ciphertext? That seems too short.
    
    print('\n[*] Trying alternative: assume ephemeral keys are implicit (from previous knowledge?)')
    print(f'[!] Gateway static pub known: {GATEWAY_STATIC_PUB.hex()[:32]}...')
    
    # Actually, wait: maybe the tap only shows ENCRYPTED parts after ephemeral keys were sent separately?
    # Or the ephemeral keys ARE 16B? Let's check X25519 specification... No, X25519 is always 32B.
    
    # Another theory: the "48B" messages are actually 32B ephemeral + 16B encrypted payload (short AEAD)
    # If so: msg1 = e_node + ct1, msg2 = e_gateway + ct2, msg3 = s_guest + ct3 + padding
    
    if len(n2g_msgs) >= 1 and len(g2n_msgs) >= 1:
        m1 = n2g_msgs[0]
        m2 = g2n_msgs[0]
        print(f'\n[*] Message 1 (n2g): len={len(m1)}B, content: {m1.hex()}')
        print(f'    Hypothesis: first 32B = e_node, rest = ct1')
        if len(m1) >= 32:
            candidate_ephemeral_pub = m1[:32]
            print(f'    Candidate e_node: {candidate_ephemeral_pub.hex()}')
            # Verify it's valid-ish (entropy check)
            bits = sum(bin(b).count('1') for b in candidate_ephemeral_pub)
            print(f'    Bit count: {bits}/256 (valid X25519 pub should have ~128)')
        
        print(f'\n[*] Message 2 (g2n): len={len(m2)}B, content: {m2.hex()}')
        print(f'    Hypothesis: first 32B = e_gateway, rest = ct2')
        if len(m2) >= 32:
            candidate_ephemeral_gw = m2[:32]
            print(f'    Candidate e_gateway: {candidate_ephemeral_gw.hex()}')
            bits = sum(bin(b).count('1') for b in candidate_ephemeral_gw)
            print(f'    Bit count: {bits}/256')
    
    # Compute h2 manually using the transcript
    print('\n[*] Attempting to compute h2 from transcript...')
    ss = crypto.SymmetricState()
    ss.mix_hash(crypto.PROTOCOL_NAME)
    ss.mix_hash(GATEWAY_STATIC_PUB)  # For initiator, mix_hash(remote_static_pub)
    
    if len(n2g_msgs) >= 1:
        m1 = n2g_msgs[0]
        if len(m1) >= 32:
            e_node = m1[:32]
            ss.mix_hash(e_node)
            # DH(es) would require guest's ephemeral private key — UNKNOWN!
            # BUT WAIT: maybe the challenge assumes we have memory.raw with these secrets?
            # Let's skip DH for now and just see what happens if we try to continue...
            ct1_part = m1[32:]
            # Encrypt-and-hash: ss.encrypt_and_hash(ct1_part)
            # This requires session key from DH, which we don't have yet!
            
    print('[!] Cannot complete h2 computation without ephemeral/private keys.')
    print('[!] We must find these somewhere — either in memory.raw or via another mechanism.')
    
    return wire_events


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    print(f'[*] Connecting to pwn.h7tex.com:{port}...')
    asyncio.run(capture_and_analyze(port))
