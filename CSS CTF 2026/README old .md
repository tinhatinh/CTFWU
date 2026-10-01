# CSSCTF 2026

Cờ dạng `CSSCTF{...}`.

## Đã giải

| Bài | Tiêu đề | Cờ |
| --- | --- | --- |
| [lamp-drill](lamp-drill/writeup.md) | Lamp Drill - Warm-up (49 điểm) | `CSSCTF{css}` |
| [maintenance-log](maintenance-log/writeup.md) | Maintenance Log - Pwn (150 điểm) | `CSSCTF{Duh_m4t3_1_4m_sl33py}` |

## Cấu trúc mỗi bài

```
<ten-bai>/
  de.md        đề nguyên văn + metadata đã xác minh (kind file, size, sha256, format cờ)
  writeup.md   lời giải: Phân tích ban đầu / Giả thuyết đã loại trừ / Chuỗi khai thác / Cờ
  notes.md     log từng bước, gồm cả nhánh sai và lý do loại
  flag.txt     đúng chuỗi cờ đã capture
  exploit.py   script tái chạy được, đọc artifact từ argv
  analysis/    script khám phá từng giai đoạn
  files/       bản sao artifact của đề, không sửa
```

## Quy ước

- Cờ chỉ được ghi khi nó xuất hiện verbatim trong output của lệnh đã chạy. Không đoán, không viết trước.
- Số liệu trong `writeup.md` phải truy vết được về một lệnh trong `notes.md`.
- Giữ lại các giả thuyết sai; phần "Giả thuyết đã loại trừ" là phần đáng đọc nhất khi quay lại sau vài tháng.
