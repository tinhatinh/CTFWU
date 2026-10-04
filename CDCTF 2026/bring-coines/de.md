# Đề bài - bring-coines

## Nguyên văn đề

```text
bring coines
500
Rev Eng
adlee7

Hi. Me sell hats. Okay, poke?

Run the old old old progrem, poke. Bring coines.

fleg look like cdctf{fleg}. -hat mouse
```

## Thông tin đã xác minh từ file

| Mục | Giá trị |
| --- | --- |
| Artifact | `files/bringcoines.exe` (copy từ: `C:/Users/Administrator/Downloads/bringcoines.exe`) |
| Kích thước | 7284057 byte |
| SHA-256 | `576db2ac5c6657189ea446c594092c7b7d0ad5d84f3246b1165d2a372b39c3c6` |
| Loại file | PE32+ executable for MS Windows 6.00 (console), x86-64, 7 sections |
| Nhiệm vụ | Vượt qua câu hỏi "how many coins" để mở `hat_menu()`, chọn mặt hàng in cờ |
| Định dạng cờ | `cdctf{...}` |

## Hướng giải (tóm tắt)

File là executable PyInstaller (Python 3.12), không có mã native đáng chú ý: boot loader chỉ gọi `PyRun_SimpleStringFlags`. Đoạn script thật nằm trong CArchive dưới dạng bytecode, đọc được bằng `marshal.loads` vì máy phân tích chạy đúng Python 3.12. `process_coines()` chỉ mở shop khi input chuỗi bằng đúng `[(H)34]`, còn `hat_menu()` sinh cờ từ một tuple số nguyên có sẵn trong hằng số của code object.

## Chạy lại lời giải

```bash
python exploit.py files/bringcoines.exe
```

Kết quả: `cdctf{h4t_M0us3_p0k3_FLAG!}` (đã lưu trong `flag.txt`). Script cần Python 3.12 để `marshal.loads` đúng bytecode của entry.

Xác minh bằng chính binary:

```bash
printf '[(H)34]\n3\n' | ./files/bringcoines.exe
```

Output thật ở `analysis/live_run.txt`, disassembly đầy đủ ở `analysis/dis_entry.txt`.
