# Prince Walk — Reverse (50 pts)

**Flag:** `CSSCTF{P12INC3_0R_P1NC3?}` · **Files:** `prince_walk` 92384 B sha256 `2d0c95f7...`

## Đề bài

Đề cho một binary Linux tên `prince_walk`: một "mô phỏng khảo sát hành tinh" nơi avatar bắt đầu ở `(1, 1)` và beacon ở `(999999, 999999)`. Cờ nằm ở đích, nhưng không có máy Linux để chạy (binary cần terminal tương tác, `isatty` từ chối pipe).

## Phân tích ban đầu

`file` báo ELF 64-bit PIE, stripped, động; entropy toàn file 7.416. `rabin2 -z` cho thấy phần chuỗi kết thúc tại `0x8a12` và sau đó là một khối 66560 byte entropy 7.98 trong `.rodata`. Imports (`tcgetattr`, `tcsetattr`, `ioctl`, `poll`, `isatty`, `prctl`, `raise`) chỉ ra một game terminal có chống debug.

Hai manh mối định hướng:

- Địa hình được sinh thủ tục, không lưu: `FUN_00102c52` dựng 16 từ bằng `rol` và `lowbias32` (`0x7feb352d`, `0x846ca68b`), tức khối 66560 byte kia không phải map.
- `66560 = 8320 * 8`, một con số tròn bất thường với ảnh hay dữ liệu nén.

## Các hướng đã loại

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Cờ là chuỗi thường trong `.rodata`**: quét `CSSCTF` trên toàn file, 0 kết quả. Loại.
2. **Khối entropy cao là dữ liệu nén**: không có magic zlib/zstd, entropy đồng đều mọi block 4 KB. Loại.
3. **Không code nào tham chiếu khối đó**: annotation của `r2` chỉ trỏ vào vùng chuỗi; khi liệt kê mọi toán hạng RIP-relative bằng capstone thì có đúng hai `lea` tại `0x2e6a` và `0x2ea3` trỏ vào `0x4a80` và `0x4a84`. Loại bỏ kết luận sai ở trên.

## Chuỗi khai thác

**Bước 1 — Định vị hàm dùng khối.** Hai `lea` nằm trong `FUN_00102c52`, và hàm mở đầu bằng

```c
if (param_1 == 999999 && param_2 == 999999) { ... }
```

nên toàn bộ payload chỉ được giải mã khi đứng ở đúng toạ độ đích. Vì vậy không cần đi bộ hai triệu bước: chỉ cần chạy lại hàm đó với `x = y = 999999`.

**Bước 2 — Khoá sinh từ toạ độ.**

```c
for (i = 0; i < 16; i++)
    A[i] = lowbias32(((i+1) * 0x9e3779b9) ^ rol(999999, i+1) ^ 999999);
key  = lowbias32((rol(999999, 19) + 999999) ^ 0xa4093822);
```

**Bước 3 — Vòng giải mã.** Với `j = 0..8319`, chỉ số bản ghi là hoán vị `idx = (217*j + 3286) mod 8320` (217 và 8320 nguyên tố cùng nhau), rồi

```python
v1 = blob[2*idx]     ^ lowbias32((j * 0x9e3779b9) ^ key)
v2 = blob[2*idx + 1] ^ lowbias32(key + j + 0x6a09e667)
```

Bốn nibble của `v1` chọn ô của bảng `A`: `s = (v1>>8)&0xf`, `a = (v1>>12)&0xf`, `b = (v1>>16)&0xf`, `r = (v1>>20)&0x1f`. Opcode `v1 & 0xff` thuộc tập `{0xff, 0xb3, 0x8b, 0x83, 0x71, 0x48, 0x12, 0x31}`; bảy opcode đầu chỉ cập nhật `A[s]`, còn `0x83` phát một byte:

```python
pos = v2 >> 25
val = (v2 ^ A[a] ^ rol(A[b], r)) & 0xff
out[pos] = val; used[pos] = 1
A[s] ^= ((pos + val) * 0x45d9f3b) & 0xffffffff
key = (j * 0x3c6ef372 + v2 + rol(A[s] ^ A[a] ^ key ^ v1, 9)) & 0xffffffff
```

Bảng `A` tiến hoá sau mỗi byte phát ra, nên không thể tách riêng từng byte.

**Bước 4 — Điều kiện nhận.** Hàm chỉ trả kết quả khi đúng 128 byte được phát ra không trùng vị trí; `out[0]` là độ dài (phải trong `1..123`), các byte `out[1..len]` phải in được, và `out[len+1..len+4]` là FNV-1a (init `0x811c9dc5`, prime `0x1000193`) của chính đoạn đó.

**Bước kiểm chứng.** Payload tự xác thực: FNV-1a tính ra `0x763cc96c`, đúng bằng 4 byte checksum mà tác giả nhét vào, nên chuỗi thu được khớp từng byte với những gì binary sẽ in ra.

## Flag

```bash
python exploit.py files/prince_walk
```

```
result: ok  (FNV 763cc96c verified, 128 emits, len=72)
FLAG: Developer:
"No you didn't."

MISSION COMPLETE

CSSCTF{P12INC3_0R_P1NC3?}
```

## Reproduce

```bash
python exploit.py files/prince_walk
```

Cần `numpy`. `analysis/text.asm` và `analysis/main.asm` là bản disassemble toàn `.text` và các hàm `main`/`FUN_00104c3`/`FUN_001051a2` dùng khi đối chiếu thứ tự phép toán.
