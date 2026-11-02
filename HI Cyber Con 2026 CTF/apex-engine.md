---
title: "Apex Engine"
category: "Pwn"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Apex Engine

## Đề bài

Apex Multi-Threaded Settlement Engine mô phỏng một hệ thống lưu ký xử lý giao dịch đồng thời. Mục tiêu là vào khu vực secure vault và đọc dữ liệu được bảo vệ. Chuỗi khai thác kết hợp race condition trong settlement với khả năng sửa đường dẫn của document slot.

## Phân tích

Thao tác settlement/rút tiền được xử lý bất đồng bộ. Nhiều yêu cầu chạy đồng thời có thể vượt qua bước kiểm tra số dư trước khi trạng thái được cập nhật, tạo double-spend. Số dư/quyền đạt được từ bước này mở đường tới giao diện vault.

Trong vault, tài liệu được tham chiếu bằng một slot có đường dẫn đích sửa được. Nếu đường dẫn không bị giới hạn vào thư mục tài liệu, chức năng stream trở thành primitive đọc file tùy ý.

## Lời giải

### 1. Khai thác race trong settlement

Gửi các thao tác settlement/rút tiền đồng thời để tạo double-spend rồi truy cập giao diện secure vault. Bản ghi lời giải xác nhận chuỗi này hoạt động với instance từ xa, nhưng không lưu đầy đủ payload và lịch xen kẽ của các request; không thể suy ra số luồng hay thời gian chờ chỉ từ tên flag.

### 2. Sửa đường dẫn document slot

Menu enclave cung cấp các lựa chọn:

```
1. Create Document Slot
2. Stream Document via Enclave
3. Edit Document Target Path
4. Return to Main Menu
```

Chọn sửa đường dẫn của slot kiểm soát được. Trong lần chạy đã ghi nhận, slot số 3 được trỏ tới `/flag`:

```
[+] Slot #3 target updated to '/flag'
```

### 3. Stream tài liệu

Chọn “Stream Document via Enclave” cho slot vừa sửa. Enclave dùng đường dẫn mới làm tài liệu của slot và trả nội dung file:

```
================ [SECURE ENCLAVE DATA STREAM] ================
hiCTF{t0ct0u_mult1thr34d_r4c3_c0nd1t10n_w1n_8d3f_a996c1e412}
==============================================================
```

## Kết quả

```
hiCTF{t0ct0u_mult1thr34d_r4c3_c0nd1t10n_w1n_8d3f_a996c1e412}
```

Kết quả trên là dữ liệu từ lần khai thác instance đã được ghi lại. Phần còn thiếu để tái hiện tự động là client tạo race ở bước settlement; không có script hoàn chỉnh trong bộ writeup này.
