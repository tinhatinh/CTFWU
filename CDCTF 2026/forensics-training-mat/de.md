# Đề bài - forensics-training-mat

## Nguyên văn đề

```text
Forensics Training Mat
250
Training Forensics
CDCTF Team

First CTF? No worries, try out our Forensics tutorial to learn about the wonderful
world of CTF forensics challenges! After you complete the quiz at the end of the
tutorial, you will get the flag to earn points here!

The flag format is cdctf{fL@g!}

NOTE: This MAT has multiple flags. ALL FIVE (5) flags need to submitted to the
CDCTF platform (here) for points.

https://cdctf.net/training/forensics.html
```

Bản mô tả trên trang tutorial (`https://cdctf.net/training/forensics.html`), ghi ngay trước Part 1:

```text
Every flag you recover while working through this MAT - from each individual
challenge step as well as the one awarded for completing the full quiz - must be
submitted separately to the CDCTF CTFd platform.
This MAT cannot be cheesed like the other Training MATs.
There is no shortcut hidden in this page's source code, and no single answer that
skips the process. Each step genuinely requires you to work through the artifact
with the appropriate tool - you must solve ALL of the challenges to get ALL of the
flags for completion.
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/suspicious.xz` (copy từ: `C:\Users\Administrator\Downloads\suspicious.xz`) |
| Kích thước | 109912 byte |
| SHA-256 | `9eed4778b09919b882670928dedcda98ac8962e95b1be338734076bdec9da9e5` |
| Loại file | XZ compressed data, checksum CRC64 |
| Sau khi `unxz` | 524288000 byte (500 MiB), 512 byte đầu là DOS/MBR boot sector => ảnh đĩa GPT |
| Partition | #0 `billy` FAT32, #1 `astrid` ext2, #2 `hwk` ext4, #3 `main` btrfs |
| File bên trong | `flag1.png` (405 B, FAT32), `flag2.jpg` (82757 B, ext2), `flag3.png` (1405 B, ext4), snapshot btrfs trong `main` |
| Nhiệm vụ | Thu đủ 5 cờ: Part 1, Part 2, Part 3, Part 4 và cờ quiz |
| Định dạng cờ | `cdctf{...}` |
| Trạng thái | 4/5 cờ. Part 2 (StegHide trong `flag2.jpg`) còn mở, xem `writeup.md` |
| Ảnh thẻ đề | không lưu được ảnh thẻ trong phiên; đề chỉ có khối text ở trên |

Ảnh đĩa giải nén 500 MiB **không** được commit: repo giữ artifact nhẹ, `exploit.py` tự giải nén vào `%TEMP%` và xoá khi chạy xong (`--keep-image` để giữ lại).

## Hướng giải (tóm tắt)

Một ảnh đĩa GPT, bốn filesystem khác nhau, mỗi filesystem chứa đúng một artifact của một part. Part 1: FAT32 -> `flag1.png` thiếu byte magic `0x89`, sửa xong đọc QR. Part 3: ext4 -> `flag3.png` là PNG 917 byte nối tiếp XZ 488 byte, tách và giải nén. Part 4: partition btrfs giữ snapshot của một file đã xoá, `strings` ra cờ plaintext. Cờ quiz nằm trong JavaScript của chính trang tutorial. Part 2 là JPEG hợp lệ cần `steghide` với passphrase, chưa có trên máy.

## Chạy lại lời giải

```bash
python exploit.py files/suspicious.xz
```

Cần `pyzbar` (hoặc `opencv-python`) để đọc QR ở Part 1; phần còn lại chỉ dùng stdlib.

Kết quả: `cdctf{A_Basic_Crimson_Disk_Exercise_in_Forensics}`, `cdctf{A_Little_XZtra_Tr3at!}`, `cdctf{d3l3te_w0_sync_h0l3y_C0W}` và `cdctf{f00rens!k_y!pP33}` (đã lưu trong `flag.txt`). Output đầy đủ của lần chạy nằm ở `analysis/run_output.txt`.
