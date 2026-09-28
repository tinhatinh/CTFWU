# notes.md - challenge "patient exfil" (capture.pcap)

Input: `C:\Users\Administrator\Downloads\capture (2).pcap` (108,604 B, sha256 3ab17689659f80efadceea1adc2eea5e9bddfcc3254ad85e89c4c75ee20bbb76)
Định dạng cờ đề yêu cầu: `H7CTF{...}`

## H1 - flag nằm rõ trong file (strings)
cmd: `node ~/.qoder/skills/ctf-solve/scripts/triage.cjs "capture (2).pcap"`
evidence: magic=libpcap LE, entropy=5.084, 87 printable runs, flag-pattern hits=0
result: DEAD - không có chuỗi cờ nào ởcleartext, dữ liệu phải được encode hoặc rải

## H2 - kênh HTTP (8080/8443)
cmd: `work/channels.py`
evidence: 8080 chỉ có 5 request line đồng nhất (/assets/app.js x28, /api/health x22, /index x20, / x19);
8443 = 19 lần `GET /api/v2/checkin` với `User-Agent: telemetry-agent/1.4`; 108 response đều `ok` (len 66)
result: DEAD - header/body không có biến thể nào, không có tiêu đề lạ, không có body khác `ok`

## H3 - dữ liệu giấu trong response DNS (TXT/CNAME)
cmd: `work/channels.py` (đọc ancount của query exfil)
evidence: `00ja3ugvcgpm3doobx.sync.cdn-telemetry-lab.net` có ancount=0, nscount=0, arcount=0;
84 answer trong file toàn bộ thuộc nhóm benign (mirror.lab.local, grafana.internal.lab, pool.ntp.org,
updates.ubuntu.com, logging.googleapis.com, api.weather.example, cdn.jsdelivr.net) và là A record ngẫu nhiên
result: DEAD - response chỉ là nhiễu; dữ liệu nằm ở phía query

## H4 - kênh độ dài/giãn cách gói (covert channel kiểu traffic-analysis)
cmd: `work/survey.py`
evidence: payload chỉ nhận 6 giá trị rời rạc {40,45,50,53,66,87}; 19 request checkin đều 87 B như nhau;
không có ICMP; timestamp exfil cách nhau 6-12 s
result: DEAD - độ dài gói không mang thông tin, nó chỉ là HTTP/DNS header

## H5 - DNS tunneling: qname = <chỉ mục 2 số><payload base32>
cmd: in ra 10 qname unique
evidence: đúng 3 qname thuộc `sync.cdn-telemetry-lab.net`:
`00ja3ugvcgpm3doobx`, `01mi4dmy3dg43tozru`, `02gi3geoldgb6q`; phần sau chỉ mục chỉ chứa ký tự `[a-z2-7]`
nên alphabet base32 bị buộc (không cần đoán); mỗi label lặp lại thành cặp, tổng 12 packet query exfil,
trải từ 5.60 s đến 47.02 s trong 148 s capture (low-and-slow)
result: PENDING -> đã xác nhận ở H6

## H6 - ghép chunk theo chỉ mục rồi base32decode
cmd: `python exploit.py "capture (2).pcap"`
evidence: blob 44 ký tự `ja3ugvcgpm3doobxmi4dmy3dg43tozrugi3geoldgb6q` -> 27 byte `H7CTF{6787b86cc777f426b9c0}`
thoả mãn cả 2 điều kiện: 44 % 8 = 4 (padding 4 dấu `=`), và ký tự cuối đúng `}` nên không bị cắt cụt;
nếu thứ tự chunk sai thì đầu ra là rác, không thể mở `{` và đóng `}` thẳng hàng như vậy
result: OK - cờ: `H7CTF{6787b86cc777f426b9c0}`

## Ghi chú môi trường
Suite `ctf-*` reference được locate thành công (`Downloads/ctf-skills-main/ctf-skills-main`),
routing dùng `ctf-forensics/network.md` hướng signal -> DNS tunnel; không cần cài thêm tool
(scapy có sẵn, không có tshark/capinfos nên mọi thứ đi qua scapy).
