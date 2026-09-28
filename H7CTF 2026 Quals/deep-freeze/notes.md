# notes.md - deep-freeze

Input đã xác minh:
- `memory.lime.zst` - 1.438.796.330 B, sha256 `dcd7cb45b26d0e7fd52734d675168a7dcb1909e16acf78ad358fe398c36b8810`
- `files/Q3_patient_records.pdf.locked` - 672 B, sha256 `5b8701fa1b328ac8...274d6b`, entropy 7.681/8
- Cờ dạng `H7CTF{...}`. Bối cảnh: máy bị freeze TRƯỚC khi cắt điện, process ransomware vẫn sống => key còn trong RAM.

## H0 - Máy không có đường giải nén zstd nào sẵn có
cmd: `7z l memory.lime.zst`; `command -v zstd unzstd`; `python -c "import zstandard"`
evidence: 7z bản này không có codec zstd ("Cannot open the file as archive"), không có `zstd` CLI,
  không có module `zstandard`; `find "C:\Program Files"` ra `Git\mingw64\bin\libzstd.dll`
result: OK - bind libzstd 1.5.7 bằng ctypes, viết `analysis/zstd_ctypes.py`, không phải cài gì

## H1 - Kiểm tra tính nguyên vẹn của file tải về
cmd: đọc 18 byte header zstd bằng ctypes `ZSTD_getFrameContentSize`
evidence: `Frame_Content_Size = 17.175.761.051` (16.00 GiB), single frame; đề ghi 661.3 MB nhưng file là 1.37 GiB
  -> chỉ khác đơn vị/bản nén, không phải tải dở. Giải nén ra đúng 17.175.761.051 B, `frame 1 complete`, không lỗi
result: OK - dump đầy đủ

## H2 - Nhận dạng định dạng ảnh bộ nhớ
cmd: `python analysis/lime.py sections _scratch/memory.raw`
evidence: 32 byte đầu `45 4d 69 4c 01 00 00 00 ...` = magic `LiME` (0x4C694D45), version 1, 5 region raw,
  tổng 16.00 GiB (region chính 0x100000-0xbd2f7ffe ~2.95 GiB + 13 GiB trên 4G)
result: OK - LiME, đi tay đôi với volatility3 được nhưng chưa cần dùng

## H3 - Cờ có nằm sẵn trong RAM không (page cache + shell history)
cmd: `python analysis/lime.py find _scratch/memory.raw "Q3_patient_records" "H7CTF{" "flag{" ".locked"`
evidence: thấy `H7CTF{bf3a8e98115450c654b4}` ở 3 nơi: stream PDF (`...) Tj ET`), biến `FLAG='...'`
  trong script dựng đề, và log shell. Kèm đó là NGUYÊN VĂN source stager `ransomware_footprint.py`:
  `key = os.urandom(32)`, `iv = os.urandom(16)`, `ct = AES.new(key, AES.MODE_CBC, iv).encrypt(plaintext + pad)`,
  `f.write(iv + ct)`, và dict `resident = {"aes_key": key, "aes_iv": iv, "cipher": AES.new(key, ECB), "note": b"kdmp-resident-do-not-swap"}`
result: PENDING - mới chỉ là grep, chưa chứng minh được nó là tiền văn của ĐÚNG file `.locked` đang có

## H4 - Carve PDF plaintext từ page cache để có known-plaintext
cmd: `python analysis/carve.py _scratch/memory.raw`
evidence: tại `0x10b021a90` có `%PDF-1.4` + đầy đủ thân PDF (catalog/pages/page/stream/font/xref).
  Phần đuôi bị cắt vì page cache của một file KHÔNG nằm liền mạch trong RAM.
  Độ dài tiền văn thật suy ra từ file: 672 = IV(16) + 656, và 656 - pad 9 = 647 byte PDF
result: OK - có `P1 = "%PDF-1.4\n1 0 obj"` làm điểm chốt cho oracle

## H5 - Anchor theo chuỗi marker của dict, quét ±64 KB
cmd: `python analysis/findkey.py _scratch/memory.raw files/Q3_patient_records.pdf.locked kdmp-resident-do-not-swap 65536`
evidence: marker xuất hiện 12 lần, đã thử 1.572.480 cửa sổ 32 byte, không có key nào thỏa oracle
result: DEAD - dict chỉ chứa CON TRỎ tới object bytes, không chứa key inline; data nằm chỗ khác trong heap

## H6 - Anchor theo chính 16 byte IV (object bytes thật)
cmd: `python analysis/findkey2.py _scratch/memory.raw files/Q3_patient_records.pdf.locked 8192`
evidence: IV `866f319940024339a78be5b443ed8289` xuất hiện 9 lần; quanh 1 trong các vị trí đó,
  cửa sổ 32 byte tại `0x120a63490` (file `0xe067852c`, **-2064 B so với object IV**) thỏa
  `D_K(C1) == P1 ^ IV`. Hợp lý: `os.urandom(32)` rồi `os.urandom(16)` được cấp phát gần nhau trong heap.
result: OK - key = `21c0780db69f7eabeb3b8dafb1810b9611916c6becdaf0b2b318d40894295d6c`

## H7 - Xác minh bằnggiải mã thật, không bằng grep
cmd: `python exploit.py _scratch/memory.raw files/Q3_patient_records.pdf.locked`
evidence: AES-256-CBC(key, IV=file[:16]) cho 656 byte; byte cuối 0x09, kiểm PKCS#7 `pt[-9:] == 9*0x09` đúng;
  tiền văn 647 byte là PDF hợp lệ trọn vẹn (`%PDF-1.4` ... `startxref 465 %%EOF`), bên trong chứa
  `Recovery token: H7CTF{bf3a8e98115450c654b4}` - khớp chuỗi tìm thấy ở H3
result: OK - CỜ: `H7CTF{bf3a8e98115450c654b4}`

## Ghi chú môi trường
- Không cài đặt gì thêm (boundary của skill `ctf-solve`): zstd qua `ctypes` + `libzstd.dll` của Git;
  AES qua `cryptography` đã có sẵn; scapy/PIL không cần dùng tới.
- volatility3 KHÔNG cần thiết ở đây: toàn bộ giải được bằng LiME parser tự viết + oracle known-plaintext.
  Nếu cần đi sâu (danh sách process, map vùng nhớ theo VMA) thì cài `python -m pip install volatility3` (phải xin phép).
- Ảnh 16 GiB để ở `_scratch/memory.raw`, ngoài thư mục writeup; xoá được, sinh lại bằng `analysis/zstd_ctypes.py`.
- Tổng thời gian: giải nén ~4 phút, quét khoá ~25 s.
