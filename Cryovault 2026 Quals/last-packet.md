---
title: "Last Packet"
category: "Forensics"
tags: ["pcap", "debug-leak"]
solve_date: "2026-10-11T04:06:00+07:00"
language: "vi"
---

# Last Packet

**Flag:** `isfcr{l33t_c0d3_tw0_sum_f0und}`  
**Artifact:** `challenge2.pcap` (13,348 bytes)

| Artifact | SHA-256 |
|---|---|
| `challenge2.pcap` | `b6f1c693be40d65df509f5830dbbacd02a2cc7f4e2418444d8a3c9fb3afb8eae` |

## Đề bài

Tìm conversation làm lộ secret trong `challenge2.pcap` rồi khôi phục flag.

## Phân tích

PCAP có 112 packet. Conversation cần xét là client `10.0.1.50:52042` tới Two Sum API `10.0.1.200:9090`. Request ở frame 56, response ở frame 58. Có thể lọc `tcp.port == 9090` và Follow TCP Stream.

```wireshark
http || tcp.port == 9090
```

## Lời giải

1. Frame 56 gửi HTTP POST có debug mode và tên developer.
2. Frame 58 trả 200 OK với `X-Debug-Level: VERBOSE`; JSON `debug` chứa `internal_key` và chỉ dẫn `enc: xor`.
3. Hex-decode `internal_key` thành ASCII Base64. Base64-decode được 30 byte; XOR từng byte với 0x42 để lấy UTF-8 flag. Các giá trị trung gian và response giữ trong các block dưới đây.

   ```http
   POST /api/v1/twosum/solve HTTP/1.1
   Host: twosum-api.internal.corp:9090
   X-Debug-Mode: enabled
   X-Developer: raj.kumar
   Content-Type: application/json

   {"nums": [24, 42, 7, 15], "target": 66}
   ```

   ```json
   {
     "status": "ok",
     "result": [0, 1],
     "debug": {
       "internal_key": "4b7a456b495441354c6e46784e68306863695a7848545931636830784e7938644a4849334c43592f",
       "enc": "xor",
       "cache_hit": false,
       "exec_time_ms": 12,
       "node": "worker-3",
       "build": "twosum-api-v2.3.1-debug",
       "heap_mb": 247,
       "gc_pause_ms": 3
     }
   }
   ```

   ```text
   KzEkITA5LnFxNh0hciZxHTY1ch0xNy8dJHI3LCY/
   ```

   ```text
   2b31242130392e7171361d217226711d3635721d31372f1d2472372c263f
   ```

   ```text
   isfcr{l33t_c0d3_tw0_sum_f0und}
   ```

## Kết quả

Flag được khôi phục từ HTTP debug response.

`isfcr{l33t_c0d3_tw0_sum_f0und}`

## Tái hiện

Mở PCAP bằng Wireshark, lọc port 9090 và lấy `debug.internal_key` từ frame 58. Python block dùng standard library tái hiện hex → Base64 → XOR 0x42 và in flag.

```python
import base64

internal_key = (
    "4b7a456b495441354c6e46784e68306863695a7848545931636830784e793864"
    "4a4849334c43592f"
)

step1 = bytes.fromhex(internal_key)
step2 = base64.b64decode(step1, validate=True)
flag = bytes(byte ^ 0x42 for byte in step2).decode("ascii")

assert flag == "isfcr{l33t_c0d3_tw0_sum_f0und}"
print("FLAG", flag)
```

```text
FLAG isfcr{l33t_c0d3_tw0_sum_f0und}
```
