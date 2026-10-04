# Forensics Training Mat - Forensics (Training, 250 điểm)

**Flag:** `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}` · `cdctf{A_Little_XZtra_Tr3at!}` · `cdctf{d3l3te_w0_sync_h0l3y_C0W}` · `cdctf{f00rens!k_y!pP33}` (4/5, Part 2 còn mở)
**Files:** `suspicious.xz`, 109912 byte, sha256 `9eed4778b09919b882670928dedcda98ac8962e95b1be338734076bdec9da9e5`

## Đề bài

MAT rèn luyện forensics của CDCTF: một file `suspicious.xz` kèm một trang tutorial chia 4 part, cuối trang có quiz. Thẻ đề báo trước có 5 cờ và cả 5 phải nộp riêng lên CTFd. Trang tutorial nói rõ không có đường tắt trong source của nó và không có câu trả lời nào bỏ qua được bước thực hành.

## Phân tích ban đầu

`file` trả về XZ, `xz -l` báo khối giải nén 500.0 MiB. Ảnh giải nén mở đầu bằng MBR bảo vệ rồi tới block "EFI PART": đây là ảnh đĩa GPT, không phải archive. Bảng partition có 4 mục, nhãn do tác giả đặt, mỗi mục một loại filesystem:

| # | Nhãn | Base (byte) | Size (byte) | Filesystem | Bằng chứng |
| --- | --- | --- | --- | --- | --- |
| 0 | `billy` | 17408 | 4982784 | FAT32 | boot sector `"mkfs.fat"`, root cluster = 2 |
| 1 | `astrid` | 5242880 | 41943040 | ext2 | superblock `0xEF53`, compat không có bit `has_journal` |
| 2 | `hwk` | 48234496 | 130023424 | ext4 | incompat `extents+64bit+flex_bg`, ro_compat `metadata_csum` |
| 3 | `main` | 179306496 | 343932928 | btrfs | magic `_BHRfS_M` tại offset 65536 |

Bốn loại này khớp đáp án câu q4 của quiz (vfat, ext2, ext4, btrfs), nên cách phân chia part/artifact của bảng trên là cách bài toán định.

Máy không có The Sleuth Kit, binwalk, steghide; WSL chỉ còn distro `docker-desktop` tối giản (không có `bash`, không có `mount`) và Docker daemon đang tắt. Nên toàn bộ parsing tự viết bằng `struct` trong Python stdlib, chỉ việc đọc QR cần `pyzbar`.

## Các hướng đã loại

1. **Quét `cdctf{` trên cả ảnh để ăn hết một lần.** Chỉ ra đúng một chuỗi, `cdctf{d3l3te_w0_sync_h0l3y_C0W}`, 6 lần trong partition `main`. Ba cờ kia không ở dạng plaintext, và cờ quiz thì không nằm trong artifact. Loại làm đường tắt chung, nhưng đây chính là lời giải Part 4.
2. **Recover `flag1.png` từ directory record đã xoá.** Record LFN của nó bị đánh dấu `0xE5` nhưng cluster = 0 và size = 0, không có dữ liệu. Bản đang sống của cùng tên cho 405 byte, trùng con số quiz hỏi ở bước "Recovering Files".
3. **Coi QR trong `flag2.jpg` là cờ.** Ảnh 610x610 giải ra một câu thách thức, không phải cờ. Phần lõi của Part 2 nằm ở lớp StegHide.
4. **Carve `flag2.jpg` từ offset tìm thấy JPEG magic.** Cách đó cho một JPEG không có EOI. Nguyên nhân thật là thuật toán đọc block: các block đi qua single indirect bị gán logical block number bằng 0, nên dữ liệu bị xáo thứ tự. Đọc theo inode cho ra 82757 byte, kết thúc bằng `FFD9`, `exiftool` nhận baseline DCT 610x610.

## Chuỗi khai thác

**Bước 1 - Part 1: FAT32, sửa magic PNG, đọc QR.** boot sector cho bytes/sector 512, sector/cluster 1, reserved 32, FAT32 dài 75 sector, root cluster 2. Entry `FLAG1 PNG` có size 405, cluster 4. Tám byte đầu của dữ liệu là `504e470d0a1a0a00`: PNG signature thiếu byte `0x89` nên toàn bộ nội dung lệch một byte sang trái, byte dôi nằm ở cuối file. Sửa = thêm `0x89` ở đầu và bỏ byte cuối. Sau khi sửa, CRC của cả 6 chunk đều khớp và `IDAT` giải nén ra đúng `1665 = 111 * 15` byte, tức không còn hỏng ở tầng khác.

```python
fixed = b'\x89' + data[:-1]          # data = 405 byte đọc từ cluster 4
w, h, bd, ct = struct.unpack('>IIBB', fixed[16:26])   # 111 x 111, bit depth 1, palette
```

Ảnh là QR version 17: 85 module, mỗi module 1 px, cộng 13 px quiet zone. Upscale 6x rồi đưa vào `pyzbar`:

```
    QR -> 'cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}'
```

**Bước 2 - Part 3: ext4, tách PNG/XZ, unxz.** `hwk` dùng extents nên phải đi qua `ext4_extent_header` (magic `0xF30A`, trường `eh_max` dễ bị bỏ sót khiến `eh_depth` đọc lệch). inode 13 tên `flag3.png`, size 1405 byte. `binwalk`/CyberChef Extract Files chỉ làm đúng một việc: cắt tại magic `FD377A585A00`.

```
    carrier=1405 byte = PNG 917 byte + XZ 488 byte (ngat ngay sau IEND)
    XZ -> 559 byte, dong cuoi: b'cdctf{A_Little_XZtra_Tr3at!}'
```

Payload 559 byte là 3 dòng charset, một đoạn lorem ipsum và dòng cuối là cờ, tức PNG 917 byte chỉ là vỏ.

**Bước 3 - Part 4: btrfs, `strings` trên partition.** `main` là phân vùng cuối và là nơi quiz hỏi về snapshot: một file đã bị xoá nhưng dữ liệu còn được giữ trong copy-on-write, cộng thêm các bản sao trong metadata. Chỉ cần quét plaintext trên cả phân vùng, không cần mount và không cần `btrfs-progs`:

```
    cdctf{d3l3te_w0_sync_h0l3y_C0W} xuat hien 6 lan, offset dau [42122663, 42155821, 42270047]
```

Sáu vị trí này là lý do câu q14 hỏi lệnh nào đã buộc việc xoá được commit trước khi rút ổ (`sync`), và câu q15 chọn `strings`: cờ vẫn đọc được thẳng từ partition.

**Bước 4 - Cờ quiz.** Trang tutorial nói không có đường tắt trong source, nhưng cờ của phần quiz thì nằm ngay trong JavaScript cuối trang, điều kiện là trả lời đủ 15 câu:

```javascript
      // Sorry buddy, there's only one free flag here. You gotta get the rest the old-fashioned way -> Solvin' the challenges!
      if (score === total) {
        resultEl.textContent = 'Congratulations! You completed the CDCTF Digital Forensics Training MAT! Here is your flag to enter on the CTFd platform: cdctf{f00rens!k_y!pP33}';
```

Bảng đáp án trích từ chính mảng `questions` trong file HTML (bản đầy đủ ở `analysis/quiz_answers.txt`): q1 `unxz`, q2 `Disk Image`, q3 `Autopsy + Volatility + losetup`, q4 `vfat + ext2 + ext4 + btrfs`, q5 `flag1.png`, q6 `405`, q7 magic bytes sai, q8 `A JPEG of a QR Code`, q9 `StegHide`, q10 `1405`, q11 `CyberChef (Extract Files) + binwalk`, q12 `XZ`, q13 `A snapshot`, q14 `sync`, q15 `strings`.

**Bước 5 - Kiểm chứng.** Mỗi số đo trong lời giải khớp một câu quiz độc lập: 405 (q6) là size của `flag1.png` trong FAT32, 1405 (q10) là size của `flag3.png` trong ext4, bốn loại filesystem (q4) đúng bằng bảng partition, và cờ Part 4 xuất hiện nhiều lần trong `main` chứ không phải trong một file đang sống. Cả 4 cờ đều là chuỗi copy từ output lệnh, không phải ghép tay.

## Part 2 còn mở

`astrid` là ext2, inode 12 tên `flag2.jpg`, 82757 byte, JPEG baseline grayscale 610x610 có `FFD9`; SHA-256 của bản trích xuất: `c798f09c73a6195fb1db2aa46a7d696e08224cd59bf57cbaae5e058bf5be1f30`. Ảnh đã lưu ở `analysis/flag2.jpg`. QR nhìn thấy trong ảnh chỉ là chuỗi thách thức, còn cờ nằm ở payload StegHide (câu q9 của quiz khẳng định đúng kỹ thuật này).

Chưa lấy được cờ vì máy không có `steghide`: `winget search steghide` và `pip download steghide` đều không có kết quả, WSL không có distro Linux nào đủ `apt`, Docker daemon đang tắt. StegHide mã hoá payload bằng khoá suy từ passphrase nên không thể tự giải bằng đọc LSB thủ công. Hướng tiếp theo, theo thứ tự chi phí tăng dần:

1. Bật Docker Desktop, chạy một container Debian/Ubuntu cài `steghide` rồi thử passphrase rỗng (`steghide extract -sf flag2.jpg -p '' -w out`).
2. Nếu passphrase rỗng fail, dùng `stegseek` với wordlist; ứng viên tự nhiên nhất là các chuỗi QR mà bài đã cho sẵn (câu thách thức trong `flag2.jpg`, đoạn chữ trong `flag3.png`).
3. Aperi'Solve chạy toàn bộ các kỹ thuật cùng lúc, nhưng phải upload artifact của bài lên bên thứ ba.

## Flag

```bash
python exploit.py files/suspicious.xz
```

```
[0] files/suspicious.xz : 109912 byte, magic fd377a585a00 (XZ) -> unxz
    -> 524288000 byte, 512 byte dau la DOS/MBR boot sector: day la DISK IMAGE, khong phai archive
[1] GPT co 4 partition
    #0 billy   base=17408       size=4982784    loai=vfat
    #1 astrid  base=5242880     size=41943040   loai=ext
    #2 hwk     base=48234496    size=130023424  loai=ext
    #3 main    base=179306496   size=343932928  loai=?

[2] Part 1 - "billy" = FAT32
    'flag1.png' : 405 byte, 8 byte dau = 504e470d0a1a0a00 (thieu 0x89 -> PNG khong mo duoc)
    them 0x89 va bo byte duoi -> PNG 111x111 1-bit, CRC hop le cho moi chunk: True
    QR -> 'cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}'

[3] Part 2 - "astrid" = ext2 (compat bit has_journal = False)
    ino=12 size=82757 -> analysis/flag2.jpg, JPEG 610x610, co EOI: True
    QR trong anh giai ra: "Don't worry, as lasy as it might feel lite challenge makers tene to ge, we hould never give you the same ihallenge twice in a row dith no meaningful differences. Ee put a lot of heart and soul into these things."
    -> day la chu thach thuc, khong phai co; co Part 2 nam trong payload StegHide

[4] Part 3 - "hwk" = ext4 (extents + 64bit + metadata_csum)
    root dir: [(11, 'lost+found'), (13, 'flag3.png')]
    carrier=1405 byte = PNG 917 byte + XZ 488 byte (ngat ngay sau IEND)
    XZ -> 559 byte, dong cuoi: b'cdctf{A_Little_XZtra_Tr3at!}'

[5] Part 4 - "main" = btrfs (superblock magic _BHRfS_M @65536)
    magic = b'_BHRfS_M'
    cdctf{d3l3te_w0_sync_h0l3y_C0W} xuat hien 6 lan, offset dau [42122663, 42155821, 42270047] (san pham cua snapshot, khong phai file song)

=== Cac co thu duoc tu artifact ===
  Part 1 (QR trong flag1.png)        cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}
  Part 3 (XZ noi them sau PNG)       cdctf{A_Little_XZtra_Tr3at!}
  Part 4 (btrfs snapshot + strings)  cdctf{d3l3te_w0_sync_h0l3y_C0W}
  Quiz (doc tu JS cua trang tutorial) cdctf{f00rens!k_y!pP33}
  Part 2 (StegHide trong flag2.jpg)  con mo: can binary steghide + passphrase
[xoa] C:\Users\ADMINI~1\AppData\Local\Temp\cdctf_forensics_disk.img
```

## Reproduce

```bash
python exploit.py files/suspicious.xz
```

Cần `numpy`, `Pillow`, `pyzbar` cho bước đọc QR (nếu thiếu `pyzbar` script tựfallback sang `cv2.QRCodeDetector`). Ảnh đĩa 500 MiB được giải nén vào `%TEMP%` và xoá khi kết thúc; thêm `--keep-image` nếu muốn giữ để kiểm tra tay bằng `binwalk`/`fls`. Toàn bộ lời giải Part 1, 3, 4 chỉ dùng `struct` trong stdlib.
