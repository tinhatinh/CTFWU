# soupOS 0: Welcome to the Kitchen - Rev Eng pwn (431 điểm)

**Cờ:** `cdctf{soupOS_is_better_than_arch}` · **Điểm:** 431 · **Tác giả:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` (source đã che) + `symbols.txt` (kmap của kernel đang chạy)

## Đề bài

Bài free flag của chuỗi 5 thẻ soupOS: một OS 32-bit "vibe-coded", đề tự nói có **bốn chỗ nó tin nhầm
thứ**, và một instance phục vụ cả năm bài. Cờ in sẵn trên thẻ để kiểm tra kênh nộp bài.

## Lời giải

**Bước 1 - Nộp cờ free.** `Start Instance` → mở URL → đăng nhập:

```text
login: cook
password: soup
```

Cờ `cdctf{soupOS_is_better_than_arch}` nằm nguyên văn trên thẻ đề, nộp trực tiếp.

**Bước 2 - Tổng quan các stage còn lại.** Handout là source thật (chỉ che chuỗi cờ trong
`src/challenge.c`), nên toàn bộ bốn mắt xích còn lại đọc được ở đây:

```text
./soupos/src/challenge.c:14:#define FLAG1 "cdctf{REDACTED_STAGE_1_________________}"
./soupos/src/challenge.c:15:#define FLAG2 "cdctf{REDACTED_STAGE_2________________}"
./soupos/src/challenge.c:16:#define FLAG3 "cdctf{REDACTED_STAGE_3________________}"
./soupos/src/challenge.c:17:#define FLAG4 "cdctf{REDACTED_STAGE_4__________________}"
```

| Stage | Primitive | Chỗ "tin nhầm" | Thẻ tương ứng |
|---|---|---|---|
| 1 | đọc file bị chặn permission | `soupyc` gọi `open()` thẳng xuống VFS, không hỏi `may()` của shell | Mise en Place |
| 2 | lên uid 0 | `AlphaSOUP-32` không salt, không key; roster `/etc/kitchen` world-readable | Salt to Taste |
| 3 | đọc kernel memory | ELF loader kiểm `p_vaddr` cho đích nhưng **không** kiểm `p_offset` cho nguồn | Bad Recipe |
| 4 | ghi kernel memory | gán chỉ số mảng không chặn chỉ số âm → ghi dưới `pool`, cướp con trỏ hàm | Too Many Cooks |

`challenge_init()` còn tự khai hai chi tiết dùng ở stage 3-4: cờ stage 3 được `kmalloc(64)` rồi ghim trên
heap (không bao giờ ghi ra đĩa), và `/prep` là bowl duy nhất `cook` ghi được:

```c
g_stage3 = (char *)kmalloc(64);
strcpy(g_stage3, FLAG3);
klog("[chal] stage3 flag pinned at %p\n", (void *)g_stage3);
```

**Bước 3 - Kiểm tra bằng harness local.** `soupctest.exe` được biên dịch từ source handout để thử lệnh soupyc trước khi chạy trên VM:

```bash
gcc -O0 -w -idirafter "../soupos/src" -o soupctest.exe stubs.c main.c \
     ../soupos/src/soupyc.c ../soupos/src/vfs.c ../soupos/src/alphasoup.c
```

`-idirafter` (không phải `-I`) là bắt buộc: handout có `src/stdio.h` riêng remap `printf` sang `doom_printf`,
dùng `-I` là harness dùng header của đề và biên dịch lỗi.

## Cờ

```text
cdctf{soupOS_is_better_than_arch}
```

## Reproduce

```bash
tar -xzf soupos-handout.tar.gz && grep -n 'FLAG[1-4]' soupos/src/challenge.c
grep -n 'may(' soupos/src/shell.c | head            # stage 1
grep -n 'hash_secret' soupos/src/users.c            # stage 2
grep -n 'p_offset' soupos/src/usermode.c            # stage 3
grep -n 'N_INDEX_SET' soupos/src/soupyc.c           # stage 4
```
