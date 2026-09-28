"""Broken Telephone - early CONTROL frame injection."""
import os, sys, json, socket, asyncio

# Load crypto module
here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)
with open(os.path.join(murmur_dir, 'murmur_crypto.py')) as f:
    exec(f.read(), globals())


async def early_inject(port, timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection failed: {ex}')
        return
    
    received_all = []
    buffer = b''
    
    # Receive initial session event
    try:
        chunk = sock.recv(4096)
        while b'\n' not in chunk and len(chunk) < 65536:
            more = sock.recv(4096)
            if not more: break
            chunk += more
        
        lines = chunk.split(b'\n')
        buffer = lines[-1]
        
        for line in lines[:-1]:
            if not line.strip(): continue
            obj = json.loads(line.decode('utf-8'))
            received_all.append(obj)
            print(f'[recv] {obj.get("event")}: {json.dumps(obj)[:100]}')
            
    except Exception as ex:
        print(f'Initial recv error: {ex}')
    
    # NOW INJECT immediately - right after session, before node sends any messages
    print('\n[*] Injecting CONTROL PROVISION (full valid structure attempt)...')
    
    # Try different variations of CONTROL frame injection:
    
    # Variation 1: Just opcode + role (what worked before but maybe needs padding)
    inv1 = {"cmd": "inject", "data": "0101"}
    
    # Variation 2: With empty cmd length field [opcode:1][role:1][len:2LE]
    inv2 = {"cmd": "inject", "data": "01010000"}
    
    # Variation 3: Try to craft what looks like authenticated frame header
    # This is purely speculative since we don't have h2 or transport keys
    
    for i, inv in enumerate([inv1, inv2], 1):
        print(f'  Sending variant {i}: {inv["data"][:32]}...' if len(inv["data"])>32 else f'  Sending variant {i}: {inv["data"]}')
        sock.send((json.dumps(inv) + '\n').encode())
        await asyncio.sleep(1)
    
    # Now collect all remaining traffic
    print('\n[*] Collecting responses...')
    
    try:
        while True:
            sock.settimeout(5)
            chunk = sock.recv(65536)
            if not chunk: break
            
            buffer += chunk
            lines = buffer.split(b'\n')
            buffer = lines[-1]
            
            for line in lines[:-1]:
                if not line.strip(): continue
                try:
                    obj = json.loads(line.decode('utf-8'))
                    received_all.append(obj)
                    
                    if obj.get('event') == 'wire':
                        dir_ = obj.get('dir')
                        hex_data = obj.get('data')
                        raw = bytes.fromhex(hex_data)
                        print(f'  [wire {dir_} {len(raw)}B] {raw[:48].hex() if len(raw)>=48 else raw.hex()}...')
                        
                        # Check for CONTROL response signature
                        if dir_ == 'g2n' and len(raw) >= 3:
                            op = raw[0]
                            if op == 0x02:  # PROVISION response opcode
                                print(f'    -> PROVISION RESPONSE DETECTED! Raw: {raw.hex()[:128]}...')
                
                except Exception as e:
                    pass
                    
    except Exception as ex:
        print(f'Response read error: {ex}')
    
    sock.close()
    
    # Save everything for analysis
    with open('early_inject_events.json', 'w') as f:
        json.dump(received_all, f, indent=2)
    print(f'\n[+] Saved {len(received_all)} events to early_inject_events.json')
    
    # Analyze for flag
    for evt in received_all:
        if evt.get('event') == 'wire' and evt.get('dir') == 'g2n':
            raw = bytes.fromhex(evt.get('data',''))
            # Look for H7CTF{} pattern in response
            if b'H7CTF' in raw:
                idx = raw.find(b'H7CTF')
                end = min(idx+50, len(raw))
                print(f'*** FLAG FOUND at offset {idx} in g2n wire! ***')
                print(f'    {raw[idx:end]}')
                return raw[idx:end].decode('ascii',errors='ignore')
    
    print('[!] No H7CTF{ flag found in responses')
    return None


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    result = asyncio.run(early_inject(port))
    if result:
        print(f'\nFinal: {result}')
