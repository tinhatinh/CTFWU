# Đề bài - maintenance-log

## Nguyên văn đề

```text
Maintenance Log
150

Our diagnostics terminal logged an anomaly during maintenance. The vendor insists
their service is fortified with stack canaries and safe from memory corruption,
but the interface IS LEAKING. Can you forge a maintenance report, bypass the
perimeter, and acquire administrative clearance?

Flag Format: CSSCTF{...}

nc 34.116.80.78 7312
```

File kèm theo: `sector01_handout.zip` (giải nén ra `chall`, `flag.txt`, `Dockerfile`).

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/chall` (từ `sector01_handout.zip`) |
| Kích thước | 14480 byte |
| SHA-256 | `de630ba8f1a3ee201c30cf450640fcef1234ee9cda62ba777ec13e2563b118e3` |
| Loại file | ELF 64-bit LSB executable, x86-64, dynamically linked, stripped, `Type: EXEC` (no-PIE) |
| Mitigation | NX (`GNU_STACK` RW), partial RELRO (không có `BIND_NOW`), canary chỉ ở `grant`/`io_setup`/`main` |
| Dịch vụ | `34.116.80.78:7312`, socat `-T30 TCP-LISTEN:7312,reuseaddr,fork` -> `EXEC:./chall,stderr`, chạy as `ctf`, image `ubuntu:24.04` |
| `files/flag.txt` | `CSSCTF{definetely_not_flag}` - cờ mồi trong handout, KHÔNG phải cờ trên server |
| Quyền đọc cờ trên server | `flag.txt` chmod 440 `root:ctf`, tiến trình chạy as `ctf` nên đọc được |
| Nhiệm vụ | gọi hàm `grant()` (code chết) để nó in nội dung `flag.txt` |
| Định dạng cờ | `CSSCTF{...}` |

## Hướng giải (tóm tắt)

`report()` đọc đúng 80 byte vào buffer 80 byte nên không tràn trực tiếp, nhưng nó gọi
`operator()` - hàm đọc 33 byte vào buffer 32 byte, dư đúng 1 byte đè lên byte thấp của
saved rbp. Vì `report()` kết thúc bằng `leave; ret`, một byte đó biến cả frame thành
điểm nhảy: `rsp = (X-0x20 & ~0xFF) + z` rồi `ret` lấy rip từ qword kế tiếp, nằm gọn
trong 80 byte ta vừa ghi. Đặt chuỗi ROP `pop rdi; ret / 0xdeadbeef / pop rsi; ret /
0xcafebabe / grant()` ở offset phù hợp là in được cờ. Offset hợp lệ phụ thuộc 8 bit
thấp của địa chỉ stack, nên khi không gọi được thì kết nối lại lấy stack mới.

## Chạy lại lời giải

```bash
python exploit.py                       # 34.116.80.78:7312
python exploit.py --probe               # gửi input lành tính, chỉ xem flow
python analysis/selftest.py             # kiểm mô hình frame offline
```

Kết quả: `CSSCTF{Duh_m4t3_1_4m_sl33py}` (đã lưu trong `flag.txt`).
