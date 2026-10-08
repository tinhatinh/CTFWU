# soupOS 1: Mise en Place - Rev Eng pwn (479 điểm)

**Cờ:** `cdctf{mise_en_place_two_paths_one_check}` · **Điểm:** 479 · **Tác giả:** soup (CDCTF)
**Handout:** `soupos-handout.tar.gz` + `symbols.txt` (dùng chung với soupOS 0)

## Đề bài

"Có một file cờ trong root bowl và bạn không đọc được. `serve /` sẽ nói cho bạn biết lý do."

## Phân tích

`serve` là lệnh liệt kê bowl **hiện tại** và không nhận tham số (`cmd_serve(void)`, `shell.c:545`), nên
đúng như thẻ đề gợi ý thì phải gõ trần; gõ `serve /` rơi vào nhánh lệnh-lạ của shell:

```text
cook@soupOS:/> serve /
No soup for you: 'serve /'

cook@soupOS:/> cd
HELLO.TXT README.TXT RECIPE.TXT SECRET.TXT FORTUNE.TXT FLAG.TXT DEMO.SC ... ETC PREP FLAG1.TXT
```

`FLAG1.TXT` có thật trong root bowl. Trong handout, chính `challenge_init()` mô tả mắt xích bị hỏng:

```c
/* Stage 1: the flag file exists, is owned by headchef, and is readable
 * only by its owner. The shell's may() honours that, so a cook is
 * refused; soupyc's open() never asks, which is the bug being taught. */
fat_chown("FLAG1.TXT", 0);
fat_chmod("FLAG1.TXT", FAT_PERM_MARK | FAT_PERM_OR | FAT_PERM_OW);
```

Đối chiếu hai đường đi của cùng một thao tác đọc:

| | đường của shell | đường của soupyc |
|---|---|---|
| vào | `pour FLAG1.TXT` → `cmd_pour` (`shell.c:595`) | `soup -c ...` → `soupyc_run` (`shell.c:618`) |
| kiểm tra | `if (!may(path,'r')) { deny(path); return; }` | **không có** |
| đọc | `fat_read()` | `vfs_open()` → `vfs_read()` |

`may()` (`shell.c:151`) là cổng permission **duy nhất** của hệ thống, và nó chỉ được gọi từ shell.
Interpreter chạy ở ring 0 gọi thẳng xuống VFS:

```c
if (strcmp(name, "open") == 0) {
    ...
    vfs_node_t *nd = vfs_open(a[0].sval, flags);   /* khong hoi may() */
```

Đúng như tên bài: **hai đường dẫn, một phép kiểm**.

## Hướng đã thử

1. **Gọn như thẻ đề: `serve /`** — shell không nhận tham số cho `serve`, nó rơi về nhánh
   `"No soup for you: '%s'"` (`shell.c:2489`). Phải dùng `serve` trần hoặc `cd <bowl>` rồi `serve`.
2. **Sửa mode bằng lệnh của shell**: `chmod`/`chown` cũng đi qua `may()` và chỉ headchef làm được.
3. **`copy`/`move` FLAG1.TXT tới `/prep` rồi đọc**: cả hai đều gọi `may(src,'r')` ở `shell.c:807`.
4. **Đoán `SVAL_LEN` để đọc cả dòng**: `read()` cắt theo `SVAL_LEN - 1`, truyền số lớn hơn cũng vô ích;
   phải truyền đúng 47 để không bị cắt mất `}`. Đã kiểm bằng harness compile từ source thật.

## Lời giải

**Bước 1 - Gọi thẳng builtin của interpreter, bỏ qua shell gate.** `pour` trong soupyc là lệnh in
(`TK_POUR`, `soupyc.c:757`), không phải lệnh shell, và `read()` giới hạn 47 byte (`SVAL_LEN - 1`),
vừa đủ một chuỗi cờ + `\n`:

```text
cook@soupOS:/> soup -c pour read(open("/FLAG1.TXT"),47)
cdctf{mise_en_place_two_paths_one_check}
```

**Bước 2 - Vì sao `soup -c` không cần nháy.** `cmd_soup` lấy `args + 2` rồi bỏ khoảng trắng, **không** cắt
chuỗi theo nháy; nên `soup -c "code"` và `soup -c code` tương đương nhau, cần giữ dấu nháy trong string literal và tránh thêm nháy bọc toàn bộ code khi nhập vào noVNC. Đây là lý do lệnh trên không có nháy. Cũng vì thế một nháy đóng bị quên cho ra lỗi parse rất khó đoán:

```text
cook@soupOS:/> soup -c pour read(open("/FLAG1.TXT),47)
soupyc: parse error (line 1): expected ')'
```

Lỗi này đã được tái lập chính xác trong harness trong quá trình kiểm tra parser.

**Bước 3 - Kiểm tra với harness local.** `soupctest.exe` biên dịch `soupyc.c` và `vfs.c` với một FAT volume giả. Kết quả xác nhận giới hạn 47 byte và đường gọi `open → read → pour`; cờ trong thử nghiệm là dữ liệu local:

```bash
./soupctest.exe 'pour read(open("/FLAG1.TXT"),47)'
```

## Kết quả

```text
cdctf{mise_en_place_two_paths_one_check}
```

Chuỗi cờ được ghi nhận trong output quét kernel memory ở stage 3, nơi `.rodata` cũng nằm trong vùng đọc. Bản ghi không có screenshot stage 1; cơ chế đọc qua soupyc được báo cáo đã nộp thành công.

## Tái hiện

```text
login: cook / soup
serve                                              # liet ke bowl hien tai (khong nhan tham so)
cd                                                 # root bowl co FLAG1.TXT
soup -c pour read(open("/FLAG1.TXT"),47)           # doc qua duong cua soupyc
```
