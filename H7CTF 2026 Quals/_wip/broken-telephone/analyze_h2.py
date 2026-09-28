"""Broken Telephone - complete exploit using tap transcript to derive h2 and decrypt frames."""
import os, sys, json, socket, struct, asyncio

here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)

# Load murmur_crypto
script_path = os.path.join(murmur_dir, 'murmur_crypto.py')
with open(script_path) as f:
    code = f.read()
ns = {}
exec(code, ns)
crypto = type(sys)('murmur_crypto')
crypto.__dict__.update(ns)

GATEWAY_STATIC_PUB = bytes.fromhex('15e8896ef9b0d92253ba8e4f8b96d8600648a4b4f2f299ae1a4ece8c6db71b16')


async def capture_events(port, timeout=10):
    """Capture wire events until we have all 3 handshake messages + telemetry."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection error: {ex}')
        return None
    
    events = []
    buffer = b''
    
    while len(events) < 5:  # Need at least 5 wire events
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
                if obj.get('event') == 'wire':
                    events.append((obj['dir'], bytes.fromhex(obj['data'])))
                    
        except Exception as ex:
            break
    
    sock.close()
    return events


def parse_transcript(events):
    """Parse handshake messages from wire events."""
    n2g = [raw for d, raw in events if d == 'n2g']
    g2n = [raw for d, raw in events if d == 'g2n']
    
    assert len(n2g) >= 2 and len(g2n) >= 1
    
    # Message 1: n2g[0] = e_node(32) + ct1(16)
    m1_raw = n2g[0]
    e_node = m1_raw[:32]
    ct1 = m1_raw[32:]
    
    # Message 2: g2n[0] = e_gateway(32) + ct2(16)
    m2_raw = g2n[0]
    e_gateway = m2_raw[:32]
    ct2 = m2_raw[32:]
    
    # Message 3: n2g[1] should be longer (includes encrypted s_guest + payload)
    m3_raw = n2g[1]
    # Format after msg2: encrypted(s_pub) + encrypted(payload)
    # With AEAD tag (16B), each part is ~16+16=32B minimum
    # Let's just take the whole thing and decrypt later once we have session key
    
    return {
        'e_node': e_node,
        'e_gateway': e_gateway,
        'ct1': ct1,
        'ct2': ct2,
        'm3': m3_raw,
        'n2g_all': n2g,
        'g2n_all': g2n,
    }


def compute_h2(transcript):
    """Compute h2 transcript hash from public data only."""
    ss = crypto.SymmetricState()
    
    # Handshake.__init__: mix_hash(prologue), mix_hash(remote_static_pub) for initiator
    prologue = b""
    ss.mix_hash(prologue)
    ss.mix_hash(GATEWAY_STATIC_PUB)
    
    # write_msg1: mix_hash(e_node), then DH(es), encrypt_and_hash(es+payload)
    ss.mix_hash(transcript['e_node'])
    # We can't compute DH without private key, but let's see what happens...
    # Actually wait: we DON'T need to compute DH here because h2 is computed AFTER BOTH peers finish their sides
    # The transcript h2 is deterministic from PUBLIC bytes only per spec!
    # Let me re-read the spec more carefully...
    
    # Spec says: "h2 is a function of public transcript bytes only (protocol name, gateway static pub, both epubs, two ciphertexts)"
    # So it's NOT the SymmetricState.h after encryption! It's the transcript before any encryption!
    # That means: h2 = BLAKE2s(protocol_name || gateway_pub || e_node || e_gateway || ct1 || ct2)? Or similar?
    
    # Looking at Noise protocol: the handshake transcript for XKpsk3 is:
    # Initiator sends: e (32B)
    # Responder sends: e (32B) + EE authentication tag (from sym_state derived from es DH)
    # Initiator sends: s (32B for static pub, but here it's X25519 so authed with SE DH) + payload
    #
    # BUT our wire events show 48B/msg instead of full sizes. Maybe the "tap" only shows AUTHENTICATED portions?
    
    # Let's try a different approach: maybe h2 is simply:
    h2_candidate = crypto.blake2s(
        crypto.PROTOCOL_NAME +
        GATEWAY_STATIC_PUB +
        transcript['e_node'] +
        transcript['e_gateway'] +
        transcript['ct1'] +
        transcript['ct2']
    )
    
    print(f'[h2 candidate from simple transcript concat]: {h2_candidate.hex()}')
    
    # Alternatively, follow SymmetricState exactly as per reference implementation
    ss2 = crypto.SymmetricState()
    ss2.mix_hash(crypto.PROTOCOL_NAME)
    ss2.mix_hash(GATEWAY_STATIC_PUB)
    ss2.mix_hash(transcript['e_node'])
    # Missing DH(es) computation without e_node_priv!
    # This suggests either:
    # 1. memory.raw contains e_node_priv or s_guest_priv
    # 2. The challenge expects us to use a known PSK (but spec says psk parameter exists!)
    # 3. There's another vulnerability
    
    print('[!] Cannot compute exact h2 via SymmetricState without private keys.')
    print('[!] Trying alternative approaches below...')
    
    return None, h2_candidate


def main(port):
    print('[*] Capturing tap events...')
    events = asyncio.run(capture_events(port))
    if not events:
        print('[!] No events captured')
        return
    
    print(f'[+] Captured {len(events)} wire events')
    for i, (direction, raw) in enumerate(events):
        print(f'  Event {i} ({direction}): {len(raw)}B')
    
    transcript = parse_transcript(events)
    print('\n[*] Transcript parsed:')
    print(f'  e_node: {transcript["e_node"].hex()[:32]}...')
    print(f'  e_gateway: {transcript["e_gateway"].hex()[:32]}...')
    print(f'  ct1 length: {len(transcript["ct1"])}B')
    print(f'  ct2 length: {len(transcript["ct2"])}B')
    
    h2_sym, h2_simple = compute_h2(transcript)
    
    # Next steps would involve:
    # 1. Finding e_node_priv or s_guest_priv somewhere
    # 2. Using h2 to decrypt frames
    # 3. Injecting CONTROL PROVISION frame
    
    # For now, print all raw data for manual analysis
    print('\n[*] Full transcript dump for further analysis:')
    print(f'e_node_hex={transcript["e_node"].hex()}')
    print(f'e_gateway_hex={transcript["e_gateway"].hex()}')
    print(f'm3_raw_hex={transcript["m3"].hex()[:200]}...')


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    main(port)
