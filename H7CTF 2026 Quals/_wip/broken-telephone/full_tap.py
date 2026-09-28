"""Full tap event collector with JSON dump for analysis."""
import os, sys, json, socket, asyncio

# Load crypto module
here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)
with open(os.path.join(murmur_dir, 'murmur_crypto.py')) as f:
    exec(f.read(), globals())


async def collect_all(port, max_seconds=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(max_seconds)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection failed: {ex}')
        return []
    
    all_events = []
    buffer = b''
    start = asyncio.get_event_loop().time()
    
    print('[*] Starting tap collection...')
    while (asyncio.get_event_loop().time() - start) < max_seconds:
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
                evt_type = obj.get('event')
                
                # Save to JSONL for later analysis
                with open('tap_events.jsonl', 'a') as f:
                    f.write(json.dumps(obj) + '\n')
                
                all_events.append(obj)
                
                if evt_type == 'wire':
                    dir_ = obj.get('dir')
                    data_hex = obj.get('data')
                    raw = bytes.fromhex(data_hex)
                    
                    # Try to detect patterns
                    hex_str = data_hex
                    
                    # Look for repeated blocks (potential padding or frame duplication)
                    if len(raw) > 200:
                        block_size = len(raw) // 10
                        blocks = [raw[i*block_size:(i+1)*block_size] for i in range(10)]
                        unique_blocks = set(bytes(b) for b in blocks)
                        print(f'[long frame {dir_} {len(raw)}B] unique blocks out of 10 samples: {len(unique_blocks)}')
                    
                    print(f'[wire {dir_} {len(raw)}B] {hex_str[:80]}...' if len(hex_str) > 80 else f'[wire {dir_} {len(raw)}B] {hex_str}')
                    
                elif evt_type == 'session':
                    print(f'[session proto={obj.get("proto")} extra={list(obj.keys())[2:] if len(obj)>2 else "none"}]')
                elif evt_type == 'ready':
                    print('[TAP READY]')
                    
        except Exception as ex:
            print(f'Recv error: {ex}')
            break
    
    sock.close()
    
    # Save all events to file
    with open('tap_full.json', 'w') as f:
        json.dump(all_events, f, indent=2)
    print(f'\n[+] Saved {len(all_events)} events to tap_full.json')
    return all_events


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    
    # Clear previous output
    if os.path.exists('tap_full.json'):
        os.remove('tap_full.json')
    if os.path.exists('tap_events.jsonl'):
        os.remove('tap_events.jsonl')
    
    asyncio.run(collect_all(port))
