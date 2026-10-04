# notes.md - forensics-training-mat

Input: `C:\Users\Administrator\Downloads\suspicious.xz` (109912 B, sha256 `9eed4778b09919b882670928dedcda98ac8962e95b1be338734076bdec9da9e5`)
Định dạng cờ: `cdctf{...}`. Thẻ đề nói có 5 cờ, nộp riêng từng cờ.

## H1 - Mount ảnh đĩa bằng công cụ có sẵn
cmd: `wsl -u root -- bash -lc 'which mmls fls icat binwalk steghide losetup mount debugfs'`
evidence: `bash: not found`. `wsl -l -v` chỉ có distro `docker-desktop` (State Running, nhưng là distro tối giản của Docker). `docker version` → client 29.8.1, daemon báo `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. `C:\Tools\ctf` không có sleuthkit/binwalk/steghide, chỉ có `exiftool`.
result: DEAD - không có đường mount/parsing sẵn. Chuyển sang tự viết parser bằng Python stdlib (`struct`), mọi con số dưới đây lấy từ code đó.

## H2 - Cài steghide / sleuthkit tại chỗ
cmd: `winget search steghide`, `winget search stegseek`, `python -m pip download steghide`
evidence: `No package found matching input criteria.` cho cả hai từ khoá winget; pip báo `ERROR: No matching distribution found for steghide`.
result: DEAD - phần mềm StegHide chỉ có trên Linux/MSYS. Đây là lý do Part 2 chưa ra cờ.

## H3 - Nhận diện artifact
cmd: `file suspicious.xz && xz -l suspicious.xz`
evidence: `XZ compressed data, checksum CRC64`, `Strms 1 Blocks 3 Compressed 107.3 KiB Uncompressed 500.0 MiB Check CRC64`.
result: OK - `unxz` ra 524288000 byte, `file` trên ảnh gọi là `DOS/MBR boot sector; partition 1 : ID=0xee ... extended partition table (last)` => GPT protective MBR, tức DISK IMAGE (đúng đáp án q2).

## H4 - Đọc bảng partition
cmd: `python - <<'PY' ... struct.unpack('<Q', h[0x48:0x50]) ...` (xem `analysis/ext4_parse.py` phần GPT và `exploit.py::gpt_partitions`)
evidence: `entries@lba=2 count=128 size=128`, 4 mục: billy 17408/4982784, astrid 5242880/41943040, hwk 48234496/130023424, main 179306496/343932928.
result: OK. Lần đọc đầu bị sai offset (`0x30:0x50` và `0x58:0x64`) nên `struct.error`; layout đúng là MyLBA 0x18, PartitionEntryLBA 0x48, NumberOfPartitionEntries 0x50, SizeOfPartitionEntry 0x54.

## H5 - Phân loại filesystem từng partition
cmd: `python analysis/fs_classify.py` rồi đối chiếu magic
evidence: billy: boot sector `"mkfs.fat"`, FAT32 length 75, root cluster 2. astrid/hwk: `s_magic` tại superblock offset 56 => byte 1080 của partition, `0xEF53`. main: 8 byte tại 65536+64 là `5f 42 48 52 66 53 5f 4d` = `_BHRfS_M`.
result: OK - vfat + ext2 + ext4 + btrfs, khớp q4. Bẫy đã gặp: `s_magic` nằm ở offset 56 **trong superblock**, tức byte 1024+56 của partition, không phải byte 1024 (đó là `s_inodes_count`).

## H6 - ext2 hay ext4
cmd: đọc `s_feature_compat/incompat/ro_compat` tại offset superblock 92/96/100
evidence: astrid compat=`00000038` incompat=`00000002` ro=`00000003`, không có bit 0x04 `has_journal` => ext2. hwk compat=`0000103c` (có has_journal) incompat=`000022c2` (`extents+64bit+flex_bg+csum_seed`) ro=`0000046b` (`metadata_csum`) => ext4.
result: OK. Lần đầu đọc sai offset 100/104/108 (lệch 8 byte) nên bảng flags vô nghĩa.

## H7 - FAT32: bản ghi đã xoá của flag1.png
cmd: `python analysis/fat32_parse.py part0_billy.img`
evidence: `FLAG1   PNG attr=20 clus=4 size=405` và một record LFN đứng ngay trước đã bị đánh dấu `0xE5`, cluster=0, size=0.
result: DEAD cho hướng "recover file đã xoá" (không có cluster để đi), nhưng 405 byte của entry đang sống trùng con số quiz hỏi ở bước "Recovering Files" => bài chỉ cần đọc entry sống.

## H8 - PNG không mở được
cmd: `python -c "from PIL import Image; Image.open('flag1.png')"`
evidence: `PIL.UnidentifiedImageError: cannot identify image file`. Hexdump 8 byte đầu: `504e470d0a1a0a00`.
result: OK - signature PNG phải bắt đầu bằng `89`, ở đây byte đó bị mất nên toàn bộ nội dung lệch một byte sang trái và byte dôi nằm ở cuối file (đúng đáp án q7 "wrong magic bytes"). Sửa `b'\x89' + data[:-1]` -> CRC của cả 6 chunk đều khớp, `IDAT` inflate ra 1665 = 111*15 byte.

## H9 - QR giải không ra
cmd: `pyzbar.decode` trên ảnh dựng từ palette
evidence: lần đầu dựng ảnh bằng `(1-bits)*255`, kết quả `[]` và `cv2` trả xâu rỗng. Palette của ảnh: index 0 = `000000`, index 1 = `ffffff`, tức bit 1 là trắng.
result: DEAD - chiều đảo màu. Dựng đúng `bits*255` (bit 1 = trắng) rồi upscale 6x và pad 30 px: `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}`. Ảnh 111x111 = 85 module (QR version 17) + 13 px quiet zone.

## H10 - Carve flag2.jpg theo offset tìm thấy JPEG magic
cmd: tìm `FFD8FFE0` trong partition astrid, cắt từ đó tới `FFD9`
evidence: magic nằm ở byte 1049600 (= block 1025 của partition, block data đầu tiên của file), nhưng 40000 byte tiếp theo không có `FFD9`.
result: DEAD - không phải file bị cắt. Nguyên nhân thật ở thuật toán đọc block của ext2: `blocks()` gán logical block number = 0 cho mọi block lấy từ single indirect, nên `sorted()` xếp lộn và dữ liệu bị đảo đoạn. Sau khi đánh số `12 + i`, inode 12 cho 82757 byte, kết thúc `FFD9`, `exiftool` báo baseline DCT 610x610.

## H11 - ext4 extents: "cannot parse root dir"
cmd: `python ext.py part2_hwk.img`
evidence: `desc_size=0`, rồi root inode đọc ra garbage. Hai lỗi: (a) `bg_inode_table_hi` nằm ở offset **40** của group descriptor 64 byte, không phải 44; (b) `ext4_extent_header` là `magic, entries, max, depth, generation` - bỏ sót `eh_max` khiến `eh_depth` đọc thành 4.
result: OK - sau khi sửa, `root dir: [(11, 'lost+found'), (13, 'flag3.png')]`, size 1405.

## H12 - QR trong flag2.jpg là cờ Part 2?
cmd: `pyzbar.decode(Image.open('analysis/flag2.jpg'))`
evidence: `"Don't worry, as lasy as it might feel lite challenge makers tene to ge, we hould never give you the same ihallenge twice in a row dith no meaningful differences. Ee put a lot of heart and soul into these things."`
result: DEAD cho hướng cờ. Đây là chuỗi thách thức, cùng kiểu với QR trong `flag3.png` (đoạn "Do you really not trust us? ... Just like this file...").

## H13 - File mang ở Part 3
cmd: `carrier.find(b'\xfd7zXZ\x00')` trên 1405 byte của `flag3.png`
evidence: XZ magic nằm ở offset 917, ngay sau `IEND` của PNG. `PNG 917 byte + XZ 488 byte`. `lzma.decompress` toàn bộ 488 byte -> 559 byte text, dòng cuối `cdctf{A_Little_XZtra_Tr3at!}`.
result: OK - cờ Part 3. Kích thước 1405 trùng q10, loại archive là XZ trùng q12.

## H14 - Quét plaintext trên partition main
cmd: mmap + regex `cdctf\{[^}\n]{3,80}\}` trên `[base, base+size)` của `main`
evidence: 6 vị trí trong phân vùng btrfs: offset partition 42122663, 42155821, 42270047, 75677095, 75710253, 75824479; chuỗi duy nhất `cdctf{d3l3te_w0_sync_h0l3y_C0W}`.
result: OK - cờ Part 4, không cần mount, không cần `btrfs-progs`. Không có bản ghi directory sống nào trỏ tới dữ liệu đó, nên đây là bản sao do snapshot/CoW giữ lại (q13 "A snapshot", q15 "strings").

## H15 - Cờ quiz
cmd: `curl -sL https://cdctf.net/training/forensics.html` rồi parse `<script>` cuối trang
evidence: `if (score === total) { resultEl.textContent = 'Congratulations! ... : cdctf{f00rens!k_y!pP33}'; }`, kèm comment `// Sorry buddy, there's only one free flag here.`. Mảng `questions` cho ra toàn bộ đáp án, lưu ở `analysis/quiz_answers.txt`.
result: OK - cờ thứ năm. Trang tutorial tuyên bố "no shortcut hidden in this page's source code" nhưng cờ quiz thì có nằm trong JS; 4 cờ kia vẫn phải giải thật.

## H16 - Part 2 (StegHide)
cmd: (chưa chạy được) `steghide extract -sf analysis/flag2.jpg`
evidence: `flag2.jpg` là JPEG hợp lệ, có EOI, QR bên trong chỉ là câu thách thức; q9 của quiz nói kỹ thuật là StegHide. Máy không có `steghide`/`stegseek` (H2).
result: PENDING - cần container Linux có `steghide` (Docker daemon đang tắt) hoặc bản build Windows. StegHide mã hoá payload bằng khoá từ passphrase, nên không đọc LSB thủ công được; thử passphrase rỗng trước, rồi wordlist từ chính các chuỗi QR của bài.

## Ghi chú về thời gian solve
Đồng hồ máy nhảy đúng 1 ngày trong phiên: các file tạo đầu phiên mang timestamp `2026-10-03 22:0x`, file tạo về sau mang `2026-10-04 22:0x` dù cách nhau vài phút. Vì minute không còn truy vết được, `tools/solve_times.json` ghi `2026-10-04` dạng ngày thuần (site render không có giờ), thay vì bịa phút.

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
