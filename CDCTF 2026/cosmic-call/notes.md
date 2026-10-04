# notes.md - cosmic-call

Hai instance đã đánh: `wigjupsh` (có `/tmp/all.pcap`, `/tmp/pass.pcap`, `.bash_history` của operator)
và `zmvopuqy` (trần: không có gì trong `/tmp`, không có history). Instance khác nhau về IP, keystream,
token; **cờ giống hệt nhau**.

## H1 - Định vị kênh liên lạc
cmd: `tcpdump -nn -r /tmp/all.pcap | awk '{print $3,$5,$NF}' | sort | uniq -c`
evidence: mọi traffic phi-ttyd là một dòng UDP duy nhất `172.25.32.3:41100 <-> 172.25.31.3:41200`
(instance 2: `172.25.190.3 <-> 172.25.189.3`); phần còn lại là ttyd 7681
result: OK - đúng một cặp endpoint, độ dài payload chỉ 10/21/25/51/53/226/227/228

## H2 - Đào traffic ttyd 7681 để tìm phiên của operator
cmd: `grep -aoE '[ -~]{12,}' /tmp/all.pcap | sort -u | head -60`; `grep -ac 'Y2RjdGY'`; `grep -aic '6364637466'`
evidence: chỉ ra mã nguồn xterm.js/zmodem/trzsz, `GET /`, `Host: 127.0.0.1:7681`, `TITLE=COSMIC-1 relay`
result: DEAD - capture không chứa I/O thiết bị đầu cuối nào, không có frame WS của client để mở khoá

## H3 - Solver của operator trong `.bash_history`
cmd: `sed -n "/^base64 -d > \/tmp\/mini.py/,/^EOF$/p" ~/.bash_history | sed '1d;$d' > /tmp/mini.b64; base64 -d /tmp/mini.b64 > /tmp/mini.py; python3 -c "import ast;ast.parse(open('/tmp/mini.py').read());print('PARSE OK')"`
evidence: `2783 B`, md5 `c73ed6bf902b53200c1c318ea4d54018`, PARSE OK
result: OK để khởi động, nhưng `mini.py` **che mất traffic thú vị**: `elif pl[:2] == M[1] and len(pl) not in (228, 227, 10)`
và dedup REQ theo `t[:14]` (chỉ in ra 2 dòng REQ). Phải bỏ filter: `sed 's/ and len(pl) not in (228, 227, 10)//'`

## H4 - Keystream khôi phục theo cột (cách của operator) có đúng không
cmd: `python3 /tmp/mini.py /tmp/all.pcap` vs `python3 /tmp/mini.py /tmp/pass.pcap`
evidence: hai pcap cho hai khoá khác nhau `ca62daa40ca2627` và `ca62daa60ca22627`; bản sai in ra
`1|stctus|repmrt|modg|nominan|...`. Trên capture tổng hợp tự sinh, 4/8 cột sai, `SIGNAL REPORT` thành `SNYLAL'TEWQPT`
result: OK nhưng phải thay bằng suy khoá từ plaintext đã biết + kiểm chứng bằng REP - xem H6

## H5 - Khối `session` 16 byte là ciphertext thứ hai để đánh two-time-pad
cmd: `sed 's/t\[:14\]/t[:]/g' /tmp/m2.py > /tmp/m3.py; python3 /tmp/m3.py /tmp/pass.pcap | grep -c '^REQ'`
evidence: `grep -ac '^REQ'` = 2; `status` và `ping` mang **cùng một** khối 16 byte
result: DEAD - không có ciphertext thứ hai để XOR; khối đó là nonce (token phiên), không phải cờ

## H6 - Header 6 byte có phải nonce không
cmd: `tcpdump -nn -r /tmp/pass.pcap -X -c 3 'udp'`; `sed '/else oth).append/i\    print(pl[:6].hex(), len(pl))' /tmp/m2.py > /tmp/m4.py`
evidence: `1065 c101 002e`, `1065 c102 002e`, ... - byte 2..3 tăng đều, byte 4..5 = `00 (len(ct)-1)`;
mỗi giá trị xuất hiện **hai lần** vì `-i any` bắt cùng frame ở `eth1 In` và `eth2 Out`
result: DEAD cho giả thuyết nonce, OK cho định dạng header: `marker | counter BE16 | 00 (len-1)`, không mã hoá

## H7 - Khoá thật, kiểm chứng độc lập
cmd: `K = xor(ct[:15], b'status\x00session\x1d')` rồi giải mã một REP
evidence: REP 21 B -> `err\x00bad\x00session` (14/15 byte ASCII); REP 227 B -> bản telemetry sạch 100%
`cosmic-1 status report. mode nominal. uptime 2289 seconds. ... accepted commands: status, ping, downlink flag.`
result: OK - `ca62daa60ca22627` (instance 1), `12fbefdadf548eba` (instance 2); keystream tuần hoàn 8 byte

## H8 - Byte lạ trong report là cột khoá hỏng
cmd: so `observed ^ expected` theo từng vị trí
evidence: `\x1a \x0c \x0c \x7f` xuất hiện ở các vị trí mà một cột khoá đơn nhất không thể tạo ra cả ba delta khác nhau
result: DEAD cho giả thuyết "khoá sai" - chúng là punctuation của bảng ký hiệu (`:` `,` escaped-space),
và cách đọc đúng là `\x7f` = dấu cách **bên trong một trường**

## H9 - Replay một REQ bắt vệ tinh nhả cờ
cmd: gửi lại nguyên văn một REQ vừa chụp
evidence (instance 1): `*** FLAG-BEARING *** 172.25.31.3:41200>172.25.31.2:47479 53 b'flag\x00CDCTF[w...'`
evidence (instance 2, ba lần đầu): chỉ nhận `err\x00bad\x00session`
result: HỠI - nguyên nhân không phải counter, mà do **tôi chép tay ciphertext sai 2 nibble**
(`ff ca` -> `bf fa`), làm hỏng 2 byte token. Nghiệm: `i = D.rfind(ct[:8]); pkt = D[i-6:i+47]` - không gõ lại nữa

## H10 - Counter phải tươi / phải là giá trị tương lai
cmd: replay `c012` (lỗi do H9), rồi `c173` (+8 bước), `c1a0` (+200 bước), `c137` verbatim
evidence: tất cả đều `err bad session` **khi ciphertext còn sai**; sau khi sửa ciphertext thì
`status` verbatim -> REP 227 (report), counter cũ cũng vẫn được trả lời
result: DEAD - counter không bị chặn replay như đã nghi; luật thật là parse số trường (xem H12)

## H11 - Cờ là bản downlink theo lịch, chỉ cần ngồi bắt
cmd: `timeout -s INT 240 tcpdump -i any -nn -s0 -w /tmp/watch.pcap 'udp and src host 172.25.189.3'`
evidence: 240 s = 80 REP 228 + 16 REP 227 + 24 pong, **không có 53 B nào**; `grep -ac cdctf` = 0 trên mọi pcap
result: DEAD - phải tự gọi lệnh, không có push thụ động

## H12 - Tên lệnh thật
cmd: `python3 /tmp/c.py` bắn 7 biến thể, bắt riêng `udp and dst host 172.25.189.2`, đọc sau khi window đóng
evidence: `downlink\x7fflag` -> REP 53 B (cờ); `downlink_flag`, `downlink flag`(0x20), `flag` -> `err unknown command`;
`downlink\x00flag` -> `err bad session` (thừa một trường, parser hỏng); `status` verbatim -> REP 227 B
result: OK - đúng như cách report viết, `0x7f` là phần tử của tên lệnh

## H13 - Đọc cờ: `@` hay `` ` ``, hoa hay thường
cmd: thử mọi tổ hợp hoa/thường của hậu tố hex + hai ký tự ở ô `0x60`
evidence: `cdctf{w3_@re...}` và `cdctf{w3_\`re...}` đều "incorrect"; bản giải mã giống hệt nhau trên hai
instance có keystream khác nhau -> phép giải đúng, nhưng **độ hoa/thường không phục hồi được từ một mẫu**
result: MỞ cho tới khi có cờ thật `cdctf{W3_@rE_n0T_AL0n3_OuT_h3r3?_5d68a0e7}`. Cách đúng là lấy nhiều
mẫu downlink rồi OR bit 5 theo vị trí (kênh chỉ XOÁ bit 5): đã kiểm chứng bằng control dương/âm trong
`analysis/twopad.py` và `exploit.py --samples`.

## Ghi chú công cụ

- `tcpdump -X 'udp[4:2] = 61'` từng in ra rỗng và suýt bị kết luận "vệ tinh không trả lời"; file có
  packet 21 B. Luôn histogram trước khi lọc theo độ dài.
- `socket.socket(); s.bind((ip,port)); s.sendto(...)` trên máy relay ném `BrokenPipeError` trước khi
  packet rời card -> pcap rỗng là lỗi của mình, không phải verdict của peer.
- Đọc pcap phải sau khi `timeout` kết thúc tcpdump, nếu không dữ liệu còn trong buffer.
- Capture tổng hợp để test: global header pcap phải 24 byte (`struct.pack("<IHHiIII", ...)`);
  dùng `<IHHiII` là 20 byte và lệch cả file.
