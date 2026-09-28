"""Broken Telephone - analyze long frames for plaintext patterns."""
import os, sys, json, re

with open('early_inject_events.json') as f:
    events = json.load(f)

print("Analyzing all wire events for plaintext patterns...\n")

for i,e in enumerate(events):
    if e.get('event') != 'wire': continue
    
    raw = bytes.fromhex(e['data'])
    d = e['dir']
    
    # Look for MURMUR magic string in telemetry
    if b'MURMUR' in raw:
        idx = raw.find(b'MURMUR')
        print(f"Event {i} ({d}, {len(raw)}B): MURMUR magic at offset {idx}")
        print(f"  Context: {raw[max(0,idx-10):idx+50]}")
        continue
    
    # Check for flag-like pattern
    if b'H7CTF' in raw or b'flag{' in raw.lower():
        idx = max(raw.find(b'H7CTF'), raw.lower().find(b'flag{'))
        print(f"Event {i} ({d}, {len(raw)}B): Flag pattern at offset {idx}")
        print(f"  Context: {raw[max(0,idx-5):idx+60]}")
        continue
    
    # Look for H7CTF{} UUID pattern anywhere in hex encoding
    hex_data = e['data']
    uuid_pattern = r'H7CTF\{[a-f0-9-]{36}\}'
    matches = list(re.finditer(uuid_pattern, hex_data, re.IGNORECASE))
    if matches:
        for m in matches:
            print(f"Event {i} ({d}, {len(raw)}B): Found H7CTF{{...}} at hex offset {m.start()}")
            print(f"  Match: {m.group()}")

# Also decode long frames as ASCII to see if anything readable
print("\n\nScanning long frames for ASCII text...")
long_frames = [(i,e) for e in events if e.get('event')=='wire' and len(bytes.fromhex(e['data'])) > 400]
for i,(idx,e) in enumerate(long_frames[:5]):
    raw = bytes.fromhex(e['data'])
    # Try to find printable ASCII sequences
    ascii_seq = re.findall(b'[\\x20-\\x7e]{8,}', raw)
    if ascii_seq:
        print(f"Frame {idx} ({len(raw)}B, dir={e['dir']}):")
        for seq in ascii_seq[:3]:
            txt = seq.decode('ascii',errors='ignore')
            if not all(c.isalnum() or c in '_-.{}' for c in txt.replace('{','').replace('}','')):
                print(f"  '{txt}'")
