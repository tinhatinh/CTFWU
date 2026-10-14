---
title: "Cubism"
category: "Reverse"
tags: ["linux-elf", "static-analysis", "quirc", "qr-code", "constraint-solving", "voxel-projection"]
solve_date: "2026-10-10"
language: "vi"
---

# Cubism

**Flag:** `FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}`
**Dịch vụ:** `ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337`. **Artifact:** `handout.zip` (18065 B), chứa `checker` (34888 B, ELF64 PIE đã strip) và `server.py` (1383 B).

## Đề bài

`server.py` nhận 441 dòng qua `sys.stdin.buffer.readline(SIDE_LENGTH + 2)`, nối chúng rồi gửi vào stdin của binary `checker`. Binary không xuất thông báo nào (stdout/stderr bị tắt, process chạy với `env={}`), nên giới hạn dòng, bảng ký tự và số voxel được kiểm tra bên trong. Exit code 0 khiến server in flag từ biến môi trường `FLAG`.

Mục tiêu: tìm một tập voxel trong grid `21×21×21` mà ảnh chiếu của nó vượt qua phép kiểm tra trong `checker`.

## Phân tích

Toàn bộ phần này là phân tích tĩnh: `checker` được decompile bằng Ghidra headless (script chạy toàn bộ hàm, output lưu trong `decomp.c` ở directory làm việc, không đi kèm writeup); `checker` không được thực thi trên máy phân tích. Binary đã strip và chỉ expose 17 symbol libc chưa resolve, nên các hàm nội bộ tự đặt tên theo địa chỉ.

Ràng buộc ở vòng đọc input, trích từ `decomp.c`:

```c
if ((int)pcVar18 != 0x15) goto LAB_001012b9;      /* mỗi dòng phải dài đúng 21 */
if (puVar19[lVar6] == '#') { puVar15 = puVar15 + 1; uVar13 = 1; }
else { if (puVar19[lVar6] != '.') goto LAB_001012b9; uVar13 = 0; }
...
if ((undefined *)0xf4 < puVar15) goto LAB_001012b9;   /* tổng '#' tích luỹ <= 244 */
```

`LAB_001012b9` là nhánh từ chối. Ba vòng lặp lồng đều giới hạn ở `0x15`; buffer ảnh tăng theo bước `0x1b9 = 441`, tương ứng grid `21 × 21 × 21`.

Khi một lớp hoàn tất, checker dựng ảnh QR:

```c
iVar3 = FUN_00101760(puVar17, 0x15c, 0x15c);         /* 0x15c = 348 */
lVar6 = FUN_001039b0(puVar17, pcVar18, puVar16 + -0x156c);
lVar6 = (*(code *)PTR_memset_00108f98)(lVar6, 0xff, 0x1d910);
```

`0x1d910 = 121104 = 348²` byte nền trắng (`0xff`); mỗi module đen là khối `12×12` pixel. Với 21 module data, kích thước khớp vùng quiet zone 4 module: `(21 + 2*4) * 12 = 348`. Jump table phần decode ở `0x6050` (`DAT_00106050`), case label array tại `0x6070..0x6088` có 6 phần tử, và `if ((uint)in_R9 < 6)` giới hạn đúng 6 chỉ số. Checker xử lý sáu ảnh, mỗi ảnh một hướng nhìn.

Chuỗi ký tự `quirc/lib/identify.c` cùng `("row[x] == from", ...)` trong `.rodata` cho thấy **quirc** được liên kết tĩnh vào binary. Ở cuối hàm:

```c
in_R8 = "%s %s %s %s %s %s";
(*(code *)PTR___snprintf_chk_00108f60)(puVar19, 0x600, 1, 0x600);
pcVar18 = "SIMON SAYS GIVE ME THE FLAG";
iVar3 = (*(code *)PTR_strcmp_00108fb0)(puVar19);
if (iVar3 == 0) { (*(code *)PTR_puts_00108f80)("Correct!"); ... return 0; }
```

Sáu payload giải mã được (mỗi slot 256 byte) nối bằng `"%s %s %s %s %s %s"` rồi `strcmp` với `"SIMON SAYS GIVE ME THE FLAG"`, một chuỗi có thật trong `.rodata`. Chuỗi đích gồm sáu từ, nên sáu mặt phải giải mã ra `SIMON`, `SAYS`, `GIVE`, `ME`, `THE`, `FLAG` theo thứ tự bộ đếm của checker.

Hai hệ quả hình học quyết định lời giải:

- Sáu ảnh chiếu trực giao của cùng một tập voxel tạo thành **ba cặp mặt đối diện**, và mỗi cặp là ảnh gương của nhau. Một mặt ảnh chiếu chỉ cần dựng một lần; ba mặt còn lại suy ra bằng phép gương.
- Phép gương vẫn phải decode thành một từ khác trong cùng thông điệp. Vì vậy, mỗi mặt QR version 1 phải decode được theo cả hai hướng đọc.

Để trả lời câu hỏi "ảnh gương cho ra gì", quirc được clone và build thành harness độc lập (`oracle/harness.c`, mặc định đọc ảnh raw `348×348`), kèm một mô hình Python tái hiện đúng đường giải mã của `lib/decode.c` (`qrmodel.py`: `reserved_cell`, thứ tự `read_data`, `mask_bit`, `read_format`, quy ước `block_syndromes`, vòng giải segment). Hai quan sát từ oracle:

- quirc đọc ảnh gương như **transpose** của ảnh gốc. Đây không phải phép xoay: cách chọn góc và lấy mẫu module ánh xạ ảnh gương thành transpose trên 208 module data.
- Một ảnh không phải QR hợp lệ bị từ chối bằng `QUIRC_ERROR_DATA_ECC`, không phải bằng lỗi định vị, nên ràng buộc thực sự nằm ở mã sửa sai chứ không ở phần xác định mã QR.

Với mỗi mặt, hai hướng đọc tạo hệ tuyến tính trên GF(2) với 208 module data chưa biết. Mỗi hướng đóng góp `56` phương trình Reed–Solomon (version 1 có 26 codeword, trong đó `26 - 19 = 7` codeword sửa lỗi, mỗi codeword 8 bit), tổng cộng `56 + 56`. Mỗi cặp `(ECC level, mask)` tạo một format class; có **308 class** đã được kiểm tra.

## Lời giải

Ba mặt được chọn, mỗi mặt mang một cặp từ liên tiếp trong chuỗi đích: `(SIMON, SAYS)`, `(GIVE, ME)`, `(THE, FLAG)`. Cách gán này được xác nhận bởi việc dịch vụ chấp nhận bức tranh cuối cùng.

Với mỗi format class, hai message được đặt lên cùng 208 biến. Các bit tự do trong segment (12/13/14 bit) và cách chia segment cho phép hai từ dùng các tập biến rời nhau. Hệ parity `56 + 56` cùng các ràng buộc bit được giải bằng Gaussian elimination trên GF(2); nghiệm được tối ưu bằng Gray-code search trên null space khi không gian đủ nhỏ, còn lại bằng greedy bit flips.

Ba mặt nghiệm có số module đen `203 / 214 / 212`. Bước cuối là bài toán phủ: tìm tập voxel `V ⊆ 21³` với `|V| ≤ 244` sao cho ba ảnh chiếu của `V` khớp chính xác ba mặt đã dựng, tức mỗi voxel đen trên một ảnh chiếu phải được "đỡ" bởi một voxel thật trong grid. Lời giải dùng tìm kiếm tham lam có lặp lại kết hợp tìm kiếm giảm chi phí trên không gian tự do của hệ GF(2) (`joint.py`, `cover*.py`, `descend*.py`), và chấp nhận chỉ khi kiểm chứng được phủ đúng.

Kết quả là `painting.txt` (9702 B): 441 dòng, mỗi dòng 21 ký tự, tổng cộng đúng 244 ký tự `#`. Kiểm tra cục bộ:

```python
from pathlib import Path
import numpy as np

raw = Path("painting.txt").read_bytes()
rows = [r for r in raw.split(b"\n") if r]
assert len(rows) == 441 and {len(r) for r in rows} == {21}
assert set(raw.replace(b"\n", b"")) <= {ord("."), ord("#")}
print("lines:", len(rows), "chars/line:", len(rows[0]), "hashes:", raw.count(b"#"))

grid = np.array([[1 if c == 35 else 0 for c in r] for r in rows], dtype=np.uint8)
vol = grid.reshape(21, 21, 21)          # 21 lớp, mỗi lớp 21 dòng
proj = [(vol.sum(axis=a) > 0) for a in (0, 1, 2)]
print("voxels:", int(vol.sum()))
print("projection black modules:", [int(p.sum()) for p in proj])
```

```text
lines: 441 chars/line: 21 hashes: 244
voxels: 244
projection black modules: [203, 214, 212]
```

Số module đen khớp ba mặt nghiệm, và `hashes: 244` nằm đúng trên trần `0xf4`. Gửi nghiệm trực tiếp:

```bash
(timeout 70 ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337 < painting.txt > ncat_out.txt)
```

`ncat_out.txt` nhận được 480 B:

```text
   A painting is more than the sum of its blocks.

Welcome, artist.
Submit your cubist painting below.
The curator will begin after the final row.

The curator smiles.
Correct!

Enjoy your flag: FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}
```

Toàn bộ phần dựng khối lập phương không phụ thuộc instance: nghiệm chỉ là một tập voxel thoả ràng buộc tĩnh của `checker`, và `server.py` không đưa bất kỳ data nào của instance vào phép kiểm tra. Chỉ bước đọc flag cuối cần một instance đang sống.

## Kết quả

```text
FortID{TH3_Cub3_15_47_th3_54m3_T1M3_4_SyMb0l_0F_51MP11C1tY_4nd_C0mpl3Xi7y}
```

Flag đọc trực tiếp từ dịch vụ đề bài. Chưa lưu phản hồi submission.

## Tái hiện

Cần Linux hoặc MSYS cho `binutils`/Ghidra, Python 3 với `numpy`, một trình build C cho quirc, và `ncat` (nmap) có hỗ trợ `--ssl`.

Hồi phục ràng buộc tĩnh từ artifact:

```console
$ unzip handout.zip
$ file handout/checker
$ strings -a handout/checker | grep -E "SIMON|%s %s"
$ readelf -hW handout/checker | grep -E "Type|Entry"
```

```text
checker: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=ced39f5ad5ffd3108c2d9118b11ffe8089b38792, for GNU/Linux 3.2.0, stripped
%s %s %s %s %s %s
SIMON SAYS GIVE ME THE FLAG
```

Dựng oracle quirc và kiểm tra hành vi ảnh gương:

```console
$ git clone https://github.com/dlbeer/quirc
$ cc -Iquirc/include -c quirc/lib/*.c -o /dev/null   # kiểm tra header
$ cc -Iquirc/include quirc/lib/*.c oracle/harness.c -o oracle/harness
$ python -c "import qrcode" # qrmodel.py cần thư viện qrcode để sinh ảnh chuẩn đối chiếu
```

Viết `oracle/harness.c` (khoảng 1.9 KB, không đi kèm writeup) theo mô tả sau: `main(argc, argv)` nhận path ảnh raw, chiều rộng và chiều cao (mặc định `img.raw`, `348`, `348`) cùng flag `d` để dump grid; hàm `quirc_new` → `quirc_resize(q, w, h)` → `quirc_begin` → `fread` đúng `w*h` byte → `quirc_end`, rồi với mỗi chỉ số `i < quirc_count(q)` gọi `quirc_extract(q, i, &code)` và `quirc_decode(&code, &data)`, in `payload_len`/`ecc_level`/`mask`/`data_type` cùng payload, hoặc in mã lỗi `quirc_decode_error_t` khi decode thất bại. Build và chạy: `cc -Iquirc/include quirc/lib/*.c oracle/harness.c -o oracle/harness` rồi `harness img.raw 348 348 d`.

Sinh nghiệm. Các tên dưới đây là các script viết trong quá trình giải và **không** đi kèm writeup này; handout chỉ có `checker` và `server.py`. Vai trò các script đã lưu: `qrmodel.py` là mô hình decoder bám theo `lib/decode.c`, `solve_face.py`/`fastsolve.py` giải hệ GF(2) cho một mặt theo một format class, `genfaces.py` sinh nhiều mặt nhẹ nhất cho mỗi cặp từ, `joint.py` tối ưu liên hợp ba mặt, `cover*.py` và `descend*.py` tìm phủ voxel `<= 244`. Toàn bộ tham số cần thiết để dựng lại đã có ở mục Phân tích (QR version 1, cặp `(ECC level, mask)` cho hai lượt đọc, `56 + 56` phương trình parity, ảnh gương được quirc đọc thành transpose, trần 244 voxel); output cuối cùng là `painting.txt`. Vì nghiệm không phụ thuộc instance, một bức tranh hợp lệ luôn có thể dựng lại offline rồi mới gửi.

Kiểm tra `painting.txt` bằng đoạn Python ở mục Lời giải, rồi gửi:

```bash
(timeout 70 ncat --ssl cubism-e41328dc5075.inst7.ctf.fortid.com 1337 < painting.txt > ncat_out.txt)
cat ncat_out.txt
```

Nếu instance đã đổi tên host, chỉ cần thay host trong lệnh `ncat`; `painting.txt` không đổi vì nghiệm không phụ thuộc instance.
