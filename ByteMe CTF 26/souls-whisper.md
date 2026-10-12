---
title: "Soul's Whisper"
category: "Reverse"
tags: ["stack-immediates", "strcmp", "radare2", "esil-emulation"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul's Whisper

**Flag:** `OWASP{th3_s0ul_st0n3_wh1sp3r}`
**Artifact:** `soul_whisper` (16184 B, ELF 64-bit, PIE, not stripped).

## Đề bài

Binary được tặng kèm (Easy, 100 điểm, 22 lời giải). Chương trình in dữ liệu gây nhiễung hiệu `SOUL STONE VAULT`, nhắc `Enter the secret phrase:`, đọc một chuỗi bằng `scanf("%63s")`, so chuỗi đó với một mật khẩu dựng sẵn trên stack; nếu khớp thì gọi `soul_stone()` in cờ qua `printf("Flag: %s\n")`. Chuỗi `strings` duy nhất chứa `OWASP` trong file là `OWASP{thH`, nên cờ không đọc được trực tiếp.

## Phân tích

`readelf`/`file` báo PIE và còn symbol table; `r2 -q -c "is" soul_whisper` cho hai hàm người dùng:

```text
34  0x0000129a 0x0000129a GLOBAL FUNC   217      main
35  0x000011c9 0x000011c9 GLOBAL FUNC   209      soul_stone
```

Đoạn kiểm tra mật khẩu trong `main@0x129a`:

```text
|           0x00001305      lea rax, [var_50h]
|           0x0000130c      lea rax, str._63s                          ; 0x20fa ; "%63s"
|           0x0000131b      call sym.imp.__isoc99_scanf
|           0x00001320      mov dword [var_55h], 0x6c756f73            ; 'soul'
|           0x00001327      mov byte [var_51h], 0
|           0x00001339      call sym.imp.strcmp
|           0x0000133e      test eax, eax
|       ,=< 0x00001340      jne 0x1349
|       |   0x00001342      call sym.soul_stone
```

Mật khẩu là `soul` (hằng số `0x6c756f73`); vì nó được dựng bằng lệnh `mov` nên không tồn tại thành chuỗi liên tục trong `.rodata`. Điều kiện nhảy vào `soul_stone` là `strcmp` trả 0.

`main` dùng `var_50h` làm buffer đọc, tức `rbp-0x50`; `soul_stone@0x11c9` cũng dùng đúng offset đó làm đích sao chép, nên không cần dò lại khung stack:

```text
/ 209: sym.soul_stone ();
|           0x000011c9      endbr64
|           0x000011cd      push rbp
|           0x000011ce      mov rbp, rsp
|           0x000011d1      add rsp, 0xffffffffffffff80
|           0x000011e4      movabs rax, 0x68747b505341574f             ; 'OWASP{th'
|           0x000011ee      movabs rdx, 0x735f6c7530735f33             ; '3_s0ul_s'
|           0x000011f8      mov qword [var_70h], rax
|           0x000011fc      mov qword [var_68h], rdx
|           0x00001200      movabs rax, 0x5f336e3074735f6c             ; 'l_st0n3_'
|           0x0000120a      movabs rdx, 0x7d72337073316877             ; 'wh1sp3r}'
|           0x00001214      mov qword [var_63h], rax
|           0x00001218      mov qword [var_5bh], rdx
|           0x0000122a      movzx eax, byte [rbp + rax - 0x70]
|           0x00001236      mov byte [rbp + rax - 0x50], dl
|           0x00001241      cmp eax, 0x1c
|           0x00001246      mov byte [var_33h], 0
```

Bốn `movabs` là bốn qword 8 byte, ghi vào `rbp-0x70`, `rbp-0x68`, `rbp-0x63`, `rbp-0x5b`. Khoảng cách giữa `rbp-0x68` và `rbp-0x63` chỉ là 5 byte, nên qword thứ ba đè lên 3 byte cuối của qword thứ hai. Vòng `for (i = 0; i <= 0x1c; i++)` sao chép 29 byte từ `rbp-0x70` sang `rbp-0x50`, sau đó đặt NUL tại `rbp-0x33` (= `rbp-0x50 + 29`).

## Lời giải

Phần ghi đè chỉ là thủ thuật giấu chuỗi; ba byte trùng nhau phải tự nhất quán, nếu không cờ sẽ bị hỏng. Kiểm tra trực tiếp từ bốn hằng số:

```python
M = [(0x68747b505341574f, -0x70), (0x735f6c7530735f33, -0x68),
     (0x5f336e3074735f6c, -0x63), (0x7d72337073316877, -0x5b)]
buf = {}
for imm, off in M:
    s = imm.to_bytes(8, "little")
    print(len(s), s)
    for k, ch in enumerate(s):
        prev = buf.get(off + k)
        if prev is not None:
            print("overlap rbp%+x" % (off + k), chr(prev), chr(ch), prev == ch)
        buf[off + k] = ch
print(bytes(buf[i] for i in range(-0x70, -0x70 + 29)))
```

```text
8 b'OWASP{th'
8 b'3_s0ul_s'
8 b'l_st0n3_'
overlap rbp-63 l l True
overlap rbp-62 _ _ True
overlap rbp-61 s s True
8 b'wh1sp3r}'
b'OWASP{th3_s0ul_st0n3_wh1sp3r}'
```

Ba vị trí chồng lấn trùng nhau ở cả ba byte, xác nhận cách dựng chuỗi là hợp lệ. Để không phụ thuộc vào suy luận tay, toàn thân `soul_stone` được mô phỏng bằng ESIL của radare2: cấp một vùng nhớ giả cho stack, đặt `rbp = 0x80000f0`, bắt đầu chạy tại `0x11e4` (ngay sau prologue và lệnh nạp canary) và dừng tại `0x124a` (ngay trước nhánh `puts`/`printf`).

```console
$ r2 -q -e bin.relocs.apply=true -c "e io.cache=true; e asm.bytes=false; \
    s 0x11c9; af; aeim 0x8000000 0x10000 stk; aeip; \
    aer rbp=0x80000f0; aer rsp=0x80000f0; aepc 0x11e4; aesu 0x124a; \
    ar rip; px 32 @ 0x8000080; px 40 @ 0x80000a0" soul_whisper
```

```text
0x0000124a
- offset -  8081 8283 8485 8687 8889 8A8B 8C8D 8E8F  0123456789ABCDEF
0x08000080  4f57 4153 507b 7468 335f 7330 756c 5f73  OWASP{th3_s0ul_s
0x08000090  7430 6e33 5f77 6831 7370 3372 7d00 0000  t0n3_wh1sp3r}...
- offset -  A0A1 A2A3 A4A5 A6A7 A8A9 AAAB ACAD AEAF  0123456789ABCDEF
0x080000a0  4f57 4153 507b 7468 335f 7330 756c 5f73  OWASP{th3_s0ul_s
0x080000b0  7430 6e33 5f77 6831 7370 3372 7d00 0000  t0n3_wh1sp3r}...
0x000000c0  0000 0000 0000 0000                      ........
```

`0x8000080 = rbp-0x70` là nguồn, `0x80000a0 = rbp-0x50` là đích và cũng là con trỏ được đưa vào `printf("Flag: %s\n")`. Bộ nhớ đích chứa đúng 29 byte cờ rồi tới NUL, giống hệt kết quả dựng tay ở trên.

## Kết quả

```text
OWASP{th3_s0ul_st0n3_wh1sp3r}
```

Cờ được khôi phục bằng phân tích tĩnh và mô phỏng ESIL trên binary đã cho; không chạy binary trên host Windows. Chưa lưu phản hồi submission.

## Tái hiện

Cần `radare2` (đã kiểm chứng trên 6.2.2, Windows x86-64) và Python 3 cho đoạn kiểm tra chồng lấn. Đặt `soul_whisper` cạnh script.

Lệnh mô phỏng (toàn bộ output ở trên lấy từ lệnh này):

```console
$ r2 -q -e bin.relocs.apply=true -c "e io.cache=true; e asm.bytes=false; \
    s 0x11c9; af; aeim 0x8000000 0x10000 stk; aeip; \
    aer rbp=0x80000f0; aer rsp=0x80000f0; aepc 0x11e4; aesu 0x124a; \
    ar rip; px 32 @ 0x8000080; px 40 @ 0x80000a0" soul_whisper
```

Lệnh xem tĩnh:

```console
$ file soul_whisper
$ r2 -q -c "is" soul_whisper | grep -E "main|soul_stone"
$ r2 -q -e bin.relocs.apply=true -c "e asm.bytes=false; s 0x11c9; af; pd 24" soul_whisper
$ strings soul_whisper | grep -c OWASP
```

Lưu đoạn Python ở mục Lời giải thành `check_overlap.py` và chạy `python check_overlap.py`; script chỉ dùng hằng số lấy từ disassembly, không cần đọc file binary.
