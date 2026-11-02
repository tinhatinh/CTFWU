---
title: "Ground Station"
category: "Hardware"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Ground Station

## Đề bài

Bộ điều khiển hỗ trợ mặt đất GSC-7 có interlock tiếp nhiên liệu bị sửa sai. Cần lấy quyền engineer từ firmware/toolkit, sửa interlock sao cho watchdog không phục hồi cấu hình lỗi, rồi hoàn tất validation để lấy token.

## Phân tích

Firmware `gsc-fw.bin` là ELF x86-64 đã strip. Hai routine đáng chú ý:

- `0x40048e` suy ra khóa 16 byte bằng LCG `state = state*0x19660d + 0x3c6ef35f`, với `key[i] = (state>>17) ^ (i*0x5b)`.
- `0x400589` xử lý access bằng 12 vòng ARX, các phép xoay 7/11/17/19/13, nonce và hằng `0x9e3779b9`; output có dạng `a^c || b^d`.

Bản viết lại routine xác thực tái tạo được anchor `image-sig=de8c1297`; lệnh `AUTH` sau đó trả `OK access=engineer`.

## Lời giải

### 1. Tìm ngưỡng bị thay đổi

Interlock đang chạy là:

```
INTERLOCK_OK expr=(TANK_TEMP <= 145) AND (TANK_PSI <= 100)
```

Ngưỡng nhiệt đã bị tăng từ 45 °C lên 145 °C, vượt hard limit 60 °C. Các interlock của bơm làm mát, van xả và van nhiên liệu không phải điểm sai trong bản ghi.

### 2. Sửa cả cấu hình hiện hành và backup

Watchdog phục hồi backup khi `runtest`; nếu chỉ sửa chương trình hiện hành thì bản backup cũ cùng trusted checksum sẽ đưa lỗi trở lại. Cập nhật biểu thức đúng rồi lưu lại backup để đồng bộ các checksum:

```
PROG SET INTERLOCK_OK (TANK_TEMP <= 45) AND (TANK_PSI <= 100)
# live_checksum = 9ebaae207f06
BACKUP SAVE
# backup = live = trusted = 9ebaae207f06
# arm_will_restore = 0, watchdog remains enabled
```

Watchdog vẫn bật, nhưng không còn lý do phục hồi cấu hình cũ: `arm_will_restore=0`.

### 3. Chạy validation

Output đã ghi nhận:

```
DATA result=SUCCESS reason=fill_target_reached_scan_51
DATA flag=hiCTF{ground_station_fueling_test_nominal_9fe94378dd}
```

## Kết quả

```
hiCTF{ground_station_fueling_test_nominal_9fe94378dd}
```

Để tái hiện bước xác thực cần firmware/toolkit của bài. Bản tóm tắt không lưu seed ban đầu của LCG và toàn bộ routine ARX, nên các địa chỉ cùng công thức rút gọn ở trên không thay thế cho implementation đầy đủ.
