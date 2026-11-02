---
title: "Quiet Upgrade"
category: "Web3"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Quiet Upgrade

## Đề bài

Một settlement proxy có thể nâng cấp implementation và quản lý treasury. Điều kiện hoàn thành là làm số dư treasury xuống dưới 1% dự trữ ban đầu, khiến `Setup.isSolved()` trả `true`.

## Phân tích

Storage layout giữa proxy và logic bị trùng:

| Slot | `SettlementProxy` | `SettlementV1` |
|---|---|---|
| 0 | `admin` | `branchOperator` |
| 1 | `implementation` | `branchRegistrar` |

Logic chạy qua `delegatecall`, nên ghi vào `branchOperator` thực chất ghi slot 0 của proxy. `registerBranch()` nhận địa chỉ operator do người gọi kiểm soát, vì vậy nó có thể ghi đè admin.

## Lời giải

### 1. Chiếm slot admin

Gọi `registerBranch()` với operator là địa chỉ do mình kiểm soát. Sau lời gọi, slot admin của proxy chứa địa chỉ này, mở quyền gọi `upgradeTo()`.

### 2. Cài implementation phù hợp kiểm tra nâng cấp

Implementation mới phải trả đúng giá trị mà proxy yêu cầu:

```
proxiableSlot() = keccak256(QU_TAG, proxy)
```

Sau khi được cài, code này chạy trong ngữ cảnh proxy. Lời gọi `treasury.release()` vì thế xuất phát từ địa chỉ settlement system mà treasury tin cậy.

### 3. Rút dự trữ

Gọi hàm rút qua proxy cho đến khi treasury còn dưới 1% số dư ban đầu. Kiểm tra `Setup.isSolved()` trước khi lấy flag qua checker.

## Kết quả

```
hiCTF{sl0t0_c0llision_then_a_qu1et_upgrade_0545bd77a4}
```

Để tái hiện cần các contract và địa chỉ instance gốc, bao gồm cách tạo `QU_TAG`, ABI của `registerBranch()` và luồng cấp phát treasury. Bản tóm tắt không kèm giao dịch hay script triển khai đầy đủ.
