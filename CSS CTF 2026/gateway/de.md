# Đề bài - Gateway

## Nguyên văn đề

```text
Gateway
199
The reboot has awakened an abandoned UPDC checkpoint guarding access to the Quantum Nexus Network. Its emergency gate still demands three proofs of clearance, but the officers who issued them vanished during The Severance. Find your way through all three doors and claim the credentials left inside.

The ticket is your team name, case-sensitive.

Flag Format: CSSCTF{CSS{...}} where CSS{...} is what you get from the netcat

nc 34.116.80.78 31337
```

**Instance:** `nc 34.116.80.78 31337` | **Category:** Web3  
**Points:** 199

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/Gate.sol`, `files/Setup.sol` (copy từ: `C:\Users\Administrator\Downloads`) |
| Kích thước | 1202 byte / 307 byte |
| SHA-256 | `e85eca9ba00d868a9b209dadea8809a2ecc17a6aeabc3557faef7d484c3389a7` / `5f5d30d19d1896f462450600c4f7e950df681a4f0b6483167e43d983eb1ec5c3` |
| Loại file | Solidity source code, UTF-8 text |
| Nhiệm vụ | Hoàn thành 3 cửa trong contract Gate: (1) gọi từ contract khác, (2) transfer ether, (3) submit password đúng |
| Định dạng cờ | `CSSCTF{CSS{...}}` |

## Hướng giải (tóm tắt)

Deploy intermediary contract (`Breaker`) để bypass `tx.origin != msg.sender` requirement, sau đó trigger `receive()` bằng ether payment và submit `keccak256("gateway to the flag")` qua storage slot reveal → set `solved=true`.

## Chạy lại lời giải

```bash
cd %TEMP%\css_gate && cat > gateway.py <<'EOF'  # netcat client
import socket, sys, time

HOST, PORT = '34.116.80.78', 31337
TEAM = open('team.txt').read().strip()

def ex(steps, total_wait=45, quiet=5):
    s = socket.create_connection((HOST, PORT), timeout=20); t=[]
    def rd():
        buf=b''; last=None; st=time.time()
        while time.time()-st<total_wait:
            s.settimeout(2)
            try: d=s.recv(65536)
            except socket.timeout:
                if buf and last and time.time()-last>quiet: break
                continue
            except Exception as e: t.append('ERR %s'%e); break
            if not d: t.append('EOF'); break
            buf+=d; last=time.time()
        t.append(buf.decode(errors='replace')); return buf
    rd(); [s.sendall((l+'\n').encode()) or t.append('>> '+l) or t.append(rd().decode()) for l in steps]
    s.close(); return t

if __name__ == '__main__':
    print(ex(['1', TEAM])[-1])  # launch (phải kill trước nếu "already running")
    print(ex(['3', TEAM])[-1])  # get flag
EOF

python gateway.py  # kill + launch → nhận credentials
python deploy.py   # compile+deploy Breaker.sol, call run()
python gateway.py  # action 3 → flag
```

Kết quả: `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}` (đã lưu trong `flag.txt`).
