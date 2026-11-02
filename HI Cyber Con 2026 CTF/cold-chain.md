---
title: "Cold Chain"
category: "Hardware"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Cold Chain

## Đề bài

Bộ điều khiển tủ lạnh ColdLink CM-900 đang ép cả sáu ngăn chạy defrost liên tục. Cần đăng nhập bằng toolkit kỹ thuật viên, sửa cấu hình để hệ thống giữ nhiệt độ đạt chuẩn trong 60 giây và lấy proof-of-repair token.

## Phân tích

Toolkit chứa field master key. Banner của CM-900 trả serial `CLX-900-SN-4417` và nonce mới cho mỗi phiên. Token xác thực được tính theo công thức của giao thức:

```
token = sha256(FIELD_MASTER_KEY | serial | nonce)[:16]
```

Hai cơ chế phối hợp làm lỗi quay lại:

- Schedule `S9 WINTER_DEFROST_ALL` có `action=force_defrost enabled=1`, giữ sáu ngăn ở trạng thái defrost, khoảng 12 °C.
- Macro `M2 AUTO_WINTERIZE` chạy `ensure_schedule` mỗi 90 giây, đích là `S9`. Chỉ tắt schedule thì macro sẽ bật lại nó.

## Lời giải

### 1. Xác thực theo từng nonce

Lấy master key từ toolkit, kết hợp với serial và nonce hiện tại để trả lời `AUTH`. Không tái sử dụng token của phiên trước vì nonce thay đổi.

### 2. Tắt cơ chế tự khôi phục cấu hình lỗi

Tắt macro trước, sau đó tắt schedule và chuyển từng ngăn về chế độ làm lạnh:

```
MACRO DISABLE M2
SCHED SET S9 enabled=0
MODE 1 cool
MODE 2 cool
MODE 3 cool
MODE 4 cool
MODE 5 cool
MODE 6 cool
```

Thứ tự này loại bỏ nguồn tự bật defrost trước khi thay đổi trạng thái vận hành.

### 3. Giữ điều kiện đạt chuẩn

Poll `STATUS` trong cùng phiên. Khi nhiệt độ xuống dưới 5 °C và giữ đủ 60 giây, controller trả token. Bản ghi ghi nhận `held=61s`; mở phiên mới vẫn thấy `compliant=1`, `held=66s`, `M2 enabled=0`, cho thấy thay đổi không bị macro hoàn tác.

## Kết quả

```
hiCTF{cold_chain_restored_defrost_cleared_3d93eb32ec}
```

Để chạy lại cần toolkit chứa master key và một instance CM-900 của bài. Công thức token ở trên là mô tả giao thức; cách mã hóa từng trường phải theo toolkit gốc.
