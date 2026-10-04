# notes.md - soupos-3-bad-recipe

Handout: `files/soupos-handout.tar.gz` (sha256 `c9fc07e2…92a1e7`) + `files/symbols.txt`
(`1e1aad7e…04b7d9`) — giống hệt stage 0/1/2. `files/leak.hex.txt` là 11 dòng hex đã gõ trên máy.

## H1 - Cờ nằm ở đâu
cmd: `grep -n 'g_stage3\|kmalloc' soupos/src/challenge.c`; log boot của instance
evidence: `g_stage3 = kmalloc(64); strcpy(g_stage3, FLAG3);` và `[chal] stage3 flag pinned at 0x17600c`;
`symbols.txt` có `00176000 b heap_arena` (mảng `.bss` 8 MB)
result: OK - cờ chỉ trong RAM nhân, không có trên đĩa → phải xin kernel tự copy ra

## H2 - Chỗ nào cho phép đọc tuỳ ý
cmd: `sed -n '108,150p' soupos/src/usermode.c`
evidence: `load_segment()` chặn `p_vaddr < USER_LO`, `va_end > USER_HI`, `va_end <= va_start`;
kiểm `p_offset` chỉ nằm trong `#ifdef NO_CHALLENGE`; bản CHALLENGE ghi rõ
`p_offset is deliberately NOT validated`; chốt bằng `memcpy(dst, buf + ph->p_offset, ph->p_filesz)`
result: OK - nguồn đọc không bị kiểm, và `buf + p_offset` là số học 32 bit → wrap được

## H3 - Page fault có chặn không
cmd: `grep -n 'map_user_page\|paging_init' soupos/src/paging.c soupos/src/usermode.c`
evidence: `paging_init` map identity toàn bộ 127 MB; `USER_LO..USER_HI = 0xC0000000..0xC8000000`;
`MAX_ELF = 256*1024`, `MAX_UPAGES = 1024` (4 MB)
result: OK - đọc vùng nhân không fault; window 2 MB nằm trong cap 1024 page

## H4 - Chọn p_offset
cmd: `python exploit.py files/leak.hex.txt`
evidence: `p_offset = 0xFFF00000` với `buf = 0x1a0000` → `read_from = 0xa0000` = **1 MB dưới buffer**;
`heap_arena 0x176000` nằm trong khoảng đó với mọi vị trí buffer hợp lệ (harness quét 3 ứng viên `buf`);
kích thước ELF 174 B nằm ở offset 84 trong file → ảnh offset `0x100054` → `0xC0100054` = `e_entry` ✓
result: OK - `CHALLENGE build: DUOC LOAD`, `NO_CHALLENGE: BI TU CHOI (p_offset > bufsz)`

## H5 - Payload tự bắt chính nó
cmd: chạy micro-VM trong `analysis/build_elf.py`
evidence: lệnh `cmp eax,0x74636463` chứa đúng chuỗi "cdct" mà vòng quét tìm; quét cả 2 MB là in ra một
hit giả từ chính payload
result: OK - giới hạn vòng quét vào 1 MB dưới buffer (`cmp esi,0x100000`)

## H6 - Không có kênh upload
cmd: `cook /unhex.elf` trên máy (usage in ra từ `user/unhex.c`)
evidence: `cook unhex.elf IN.HEX OUT.ELF`; soupyc không viết được byte NUL nên phải đi bằng hex text + `jot`
result: OK - 11 dòng × 32 ký tự hex; `/unhex.elf` in `wrote 174 bytes` → chính là phép kiểm tra toàn vẹn
(173/175 nghĩa là gõ lệch một ký tự)

## Control đã chạy (trong `analysis/build_elf.py`)

```text
WRAP -1MB                      hits=1   (duong)
NO WRAP (p_offset = 0)         hits=0   (am: co le nhưng khong wrap thi khong thay)
WRAP, flag absent              hits=0   (am: khong co co thi khong duoc in ra gi)
ALL SCENARIOS OK
```

## Kết quả trên máy

```text
cook@soupOS:/> cook /unhex.elf /prep/LEAK.HEX /prep/LEAK.ELF
unhex: wrote 174 bytes
cook@soupOS:/> cook /prep/LEAK.ELF
cdctf{bad_recipe_the_loader_reads_wide}
cdctf{mise_en_place_two_paths_one_check}
```

Dòng thứ hai là FLAG1 (nằm trong `.rodata`) → xác nhận primitive là đọc kernel memory thật.
