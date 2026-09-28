"""Broken Telephone - try injecting CONTROL PROVISION frame directly into g2n stream."""
import os, sys, json, socket, asyncio, struct

here_dir = os.path.dirname(os.path.abspath(__file__))
murmur_dir = os.path.join(here_dir, 'files')
sys.path.insert(0, murmur_dir)

with open(os.path.join(murmur_dir, 'murmur_crypto.py')) as f:
    exec(f.read(), globals())


async def connect_and_inject(port, timeout=30):
    """Connect to tap, capture first few messages, then inject CONTROL frame."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(('pwn.h7tex.com', port))
    except Exception as ex:
        print(f'Connection failed: {ex}')
        return
    
    # First, receive initial events
    received_events = []
    buffer = b''
    
    print('[*] Capturing initial traffic...')
    for _ in range(5):
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
                received_events.append(obj)
                
                if obj.get('event') == 'wire':
                    dir_ = obj.get('dir')
                    hex_data = obj.get('data')
                    raw = bytes.fromhex(hex_data)
                    print(f'[received {dir_} {len(raw)}B]')
                    
        except Exception as ex:
            print(f'Recv error: {ex}')
            break
    
    # Now try injecting a CONTROL PROVISION frame
    # Frame structure: [masked_len:2LE][body] where body=[type:1][AEAD(payload)]
    # For CONTROL: type=0x01, payload=[opcode:1][role:1][cmd_len:2LE][cmd]
    # But we need h2 and transport keys for AEAD encryption!
    
    # Alternative theory: maybe gateway is vulnerable to unauthenticated commands?
    # Try sending raw bytes that look like a CONTROL frame without proper masking/AEAD
    
    print('\n[*] Attempting to inject CONTROL PROVISION...')
    
    # Minimal CONTROL frame attempt (unencrypted, unmasked - probably wrong but worth trying)
    # opcode=0x01 PROVISION, role=0x01 admin, empty command
    control_raw = bytes([0x01, 0x01])  # opcode + role, no cmd (empty payload is keepalive but with opcode)
    
    # Add data event with our injection
    injection_hex = control_raw.hex()
    inject_event = {"cmd": "inject", "data": injection_hex}
    
    print(f'[sending injection] {json.dumps(inject_event)}')
    sock.send(json.dumps(inject_event) + '\n')
    
    # Give gateway time to respond
    await asyncio.sleep(2)
    
    # Check for new wire events from gateway
    more_buffer = b''
    try:
        while True:
            sock.settimeout(2)
            chunk = sock.recv(4096)
            if not chunk:
                break
            more_buffer += chunk
            lines = more_buffer.split(b'\n')
            more_buffer = lines[-1]
            
            for line in lines[:-1]:
                if not line.strip():
                    continue
                obj = json.loads(line.decode('utf-8'))
                if obj.get('event') == 'wire':
                    dir_ = obj.get('dir')
                    hex_data = obj.get('data')
                    raw = bytes.fromhex(hex_data)
                    print(f'[response {dir_} {len(raw)}B] {raw[:64].hex()}...')
                    
    except Exception as ex:
        print(f'Post-injection read error: {ex}')
    
    sock.close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 41372
    asyncio.run(connect_and_inject(port))
