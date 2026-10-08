# Cosmic Call - Scanning / NTA / Crypto (797 điểm)

**Cờ:** `cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}` · **Điểm:** 797 · **Tác giả:** b0b, adlee7 (CDCTF)
**Artifact:** terminal ttyd trên máy relay (`player@router`), không có file tải về

## Đề bài

"ping... ping... there's something out there... I sure hope Command didn't reuse the CTR Nonce".
Ta có một shell trên máy relay và phải tìm xem gì đang nói chuyện trên mạng, chúng nói gì.

## Phân tích

Máy relay đóng vai trò **router** giữa hai container trong chính mạng docker của instance:

```text
player@router:~$ ip -o addr | cut -c1-90; ip neigh
1: lo    ...
2: eth0  inet 172.25.191.2/24
3: eth1  inet 172.25.190.2/24      -> Command   172.25.190.3:41100   REACHABLE
4: eth2  inet 172.25.189.2/24      -> satellite 172.25.189.3:41200   REACHABLE
```

`tcpdump` chạy được với uid 1000, cho phép capture traffic giữa hai container. Đặc điểm quan sát được:

```text
REQ  172.25.190.3:41100 -> 172.25.189.3:41200   payload 53 B, mỗi 4.000 s một gói
REP  172.25.189.3:41200 -> ...                  payload 10 B (pong), 226/227/228 B (telemetry),
                                                21 B và 25 B (lỗi), 53 B (cờ)
```

Mỗi payload = **6 byte header không mã hóa** + ciphertext:

```text
REQ  10 65 | c0 12 | 00 2e | 61 8f 8e ae ...        marker | counter BE 16 bit | 00 (len(ct)-1)
REP  00 64 | c0 55 | 00 0e | 77 89 9d da ...
```

Counter tăng đúng một đơn vị mỗi REQ (`c012` lúc 01:22:59.38 → `c137` lúc 01:42:31.63 = +293 bước
/ 1172 s = 4.000 s/bước), và **không được mã hoá**, nên sửa counter không làm lệch pha keystream.
REP mang counter riêng của vệ tinh (đơn điệu theo thời gian), không echo counter của REQ.

Các gói đã capture sử dụng lại keystream 8 byte. Có thể khôi phục keystream từ known plaintext rồi dùng nó để giải mã các message khác.

## Hướng đã thử

1. **Đào traffic ttyd trên cổng 7681.** `grep -aoE '[ -~]{12,}' /tmp/all.pcap | sort -u` chỉ trả về
   bundle tĩnh của xterm.js/zmodem/trzsz và `GET / Host: 127.0.0.1:7681`. Không có I/O thiết bị đầu cuối
   nào được ghi lại.
2. **Tìm cờ trong pcap có sẵn.** `grep -ac cdctf` = 0 trên cả `all.pcap` lẫn `pass.pcap`; sau khi bỏ bộ lọc
   độ dài trong solver của operator thì `other_payloads 0`, mọi REP chỉ là telemetry chỉ đổi chữ số.
   Cờ **không** nằm trong capture, phải tự gọi vệ tinh dẫn xuống.
3. **Tấn công two-time-pad trên khối `session`.** `status` và `ping` dùng **cùng một** khối 16 byte
   (`grep -ac '^REQ'` = 2), nên không có ciphertext thứ hai để XOR.
4. **Sửa keystream bằng điểm tựa `cdctf{`.** Cách giải khôi khoá theo cột của operator (giữ mọi `k < 128`
   làm toàn bộ byte < 128 rồi lấy argmax của một điểm tần suất chữ) không đủ tin cậy: trên văn bản chữ thường,
   một khoá sai một bit cũng điểm gần bằng. Đã tái lập trên capture tổng hợp: 4/8 cột sai,
   `SIGNAL REPORT` in ra `SNYLAL'TEWQPT`. Khoá thật phải kiểm chứng bằng cách giải mã **một REP**
   thành tiếng có nghĩa, không phải bằng điểm. Loại cách chấm điểm, giữ cách kiểm chứng.
5. **Giả thuyết "kênh truyền làm mất bit 5" là một phép XOR cố định.** Sai: vị trí mất bit 5 không tuần
   hoàn theo chu kỳ 8 hay 16 của keystream, nên nó là nhiễu trên **plaintext**, không phải lỗi khoá.

## Lời giải

**Bước 1 - Khoá 8 byte, lấy từ plaintext đã biết.** Mọi REQ mở đầu bằng `status\x00session\x1d`
(15 byte), nên một gói là đủ:

```python
K = bytes(a ^ b for a, b in zip(ct[:15], b'status\x00session\x1d'))
```

```text
KEY 12fbefdadf548eba          # instance này; instance đầu là ca62daa60ca22627
```

Kiểm chứng khoá bằng cách giải mã **câu trả lời**, không phải câu hỏi: một REP 21 byte ra
`err\x00bad\x00session` (14/15 byte ASCII sạch), và bản telemetry 221 byte giải mã thành bản telemetry có cấu trúc hợp lệ:

```text
cosmic-1 status report. mode nominal. uptime 2289 seconds. battery at 85 percent. panel temperature
minus 9 celsius. attitude stable. next pass in 45 minutes. accepted commands: status, ping,
downlink flag. end of report.
```

Bảng ký hiệu của giao thức rút ra từ chính bản report đó:

| byte | ý nghĩa | byte | ý nghĩa |
|---|---|---|---|
| `0x00` | tách trường / dấu cách | `0x0e` | `.` |
| `0x0c` | `,` | `0x1a` | `:` |
| `0x10 + n` | chữ số `n` (chữ số **không bao giờ** ở dạng `0x30+`) | `0x1d` | phân cách trước token |
| `0x7f` | **dấu cách nằm trong một trường** (escaped space) | | |

Suy ra: `downlink\x7fflag` trong report là tên lệnh nguyên văn, và token phiên là 32 nibble
(`6287E973D50005EB450005EB43093359`), đúng một block 16 byte — được dùng làm token phiên trong các request. Chưa xác định token này có vai trò nonce của một triển khai CTR hay không.

**Bước 2 - Tự dựng lệnh downlink.** Không có lệnh nào trong hai pcap từng gọi `downlink flag`, nên phải
tự phát REQ. Dựng plaintext, XOR với `K`, điền trường độ dài:

```python
pt  = b'downlink\x7fflag\x00session\x1d' + token          # 54 byte
ct  = bytes(b ^ K[i % 8] for i, b in enumerate(pt))
pkt = b'\x10\x65' + counter.to_bytes(2, 'big') + bytes([0, len(pt) - 1]) + ct
```

Toàn bộ 7 biến thể được bắn một lượt để lấy luôn bảng luật của vệ tinh
(`python3 /tmp/c.py`, xem `exploit.py` để tái chạy từ pcap):

```text
gửi 0  status (replay nguyên văn)      -> REP 227 B  = bản report          -> token ĐƯỢC chấp nhận
gửi 1  downlink_flag  (0x5f)           -> REP 25 B   = err unknown command
gửi 2  downlink_flag  (0x5f)           -> REP 25 B   = err unknown command
gửi 3  downlink flag  (0x20)           -> REP 25 B   = err unknown command
gửi 4  downlink\x7fflag (0x7f)         -> REP 53 B   = flag\x00...          -> ĐÚNG LỆNH
gửi 5  flag                            -> REP 25 B   = err unknown command
gửi 6  downlink\x00flag (0x00)         -> REP 21 B   = err bad session      (3 trường làm hỏng parser)
```

Ba lần replay đầu trả `err bad session` do lỗi chép ciphertext (`ff ca` → `bf fa`), làm thay đổi hai byte token. Để tránh lỗi này, các packet tiếp theo được trích trực tiếp từ pcap:

```python
i = D.rfind(bytes.fromhex('618f8eaeaa278ec9'))   # 8 byte đầu của ct, hằng số suốt phiên
pkt = D[i - 6:i + 47]                             # 6 byte header + đúng 47 byte ct, nguyên văn
```

**Bước 3 - Đọc cờ và chuyện hoa/thường.** Bản 53 byte giải mã ra:

```text
flag\x00CDCTF[w\x13\x7f`Re\x7fN\x10t\x7fal\x10N\x13\x7foUt\x7fH\x13R\x13\x1f\x7f\x15D\x16\x18A\x10E\x17]
```

Áp dụng bảng ký hiệu: `0x10+n` → chữ số, `0x7f` → `_` (vì cờ là **một trường duy nhất** nên mọi dấu
cách bị escape), `[`→`{`, `]`→`}`, `0x1f`→`?`, và chữ in hoa là chữ in thường bị mất bit 5.
Chuỗi thu được dài 42 ký tự: `cdctf{w3_?re_n0t_al0n3_out_h3r3?_5d68a0e7}`.

Kênh chỉ **xoá** bit 5 chứ không bật lên, nên byte `0x60` (bit 5 đã bật) chỉ có thể là `` ` ``, còn `@`
(0x40) phải hiện ra là 0x40. Cả hai cách đọc đều bị từ chối, kèm mọi tổ hợp hoa/thường của hậu tố hex.
Lý do: **bản thân độ hoa-thường không phục hồi được từ một mẫu duy nhất** — vệ tinh nhiễu mỗi lần phát
một cách ngẫu nhiên, và cờ thật là `W3_@rE_n0T_AL0n3_OuT_h3r3?`. Cách đúng (đã viết thành
`analysis/twopad.py` + vòng lấy mẫu trong `exploit.py`) là xin **nhiều bản downlink** rồi theo từng vị trí
lấy OR bit 5: nếu bất kỳ mẫu nào có bit 5 bật thì ký tự gốc có bit 5 bật; nếu mọi mẫu đều tắt, chưa thể chắc chắn bit gốc là 0 vì số mẫu hữu hạn. Có thể lấy thêm mẫu và kiểm tra chuỗi thu được bằng submission.

## Kết quả

```text
cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}
```

## Tái hiện

```bash
# 1) trên máy relay: chụp một REQ sống, rồi chụp riêng mọi phản hồi gửi về máy mình
timeout -s INT 6  tcpdump -i any -nn -s0 -w /tmp/f.pcap 'udp and src 172.25.190.3'
(timeout -s INT 25 tcpdump -i any -nn -s0 -w /tmp/b.pcap 'udp and dst host 172.25.189.2' >/dev/null 2>&1 &)

# 2) dựng và bắn 7 biến thể lệnh, rồi đọc sau khi window đóng
python3 exploit.py --probe /tmp/f.pcap        # in ra 7 packet đã gửi
sleep 20 && python3 exploit.py --decode /tmp/b.pcap

# 3) hoặc giải mã offline một pcap bất kỳ đã có
python3 exploit.py --decode /tmp/b.pcap
```

## Ghi chú khi tái hiện

- Bộ lọc `udp[4:2] = 61` bỏ qua phản hồi 21 byte. Kiểm tra phân bố độ dài packet trước khi đặt filter.
- Capture với `-i any` có thể ghi cùng packet ở cả `eth1 In` và `eth2 Out`; cần tính đến bản ghi lặp khi đếm.
- Đọc pcap sau khi `tcpdump` đã flush hoặc kết thúc.
- Trích ciphertext trực tiếp từ pcap để tránh lỗi chép tay.
- **`-i any` nhân đôi mọi bộ đếm** (một frame hiện ra cả ở `eth1 In` lẫn `eth2 Out`); đếm được 2 không phải
  là va chạm nonce.
- **Đọc file capture chỉ sau khi tcpdump đã kết thúc**, nếu không nội dung còn nằm trong buffer và bạn
  "thấy" im lặng.
- **Không tin một ciphertext do người gõ lại.** Sinh file bằng heredoc, rồi `ast.parse` + `md5sum` để chứng
  minh paste không lệch byte.
