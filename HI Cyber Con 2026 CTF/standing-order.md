---
title: "Standing Order"
category: "Web3"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Standing Order

## Đề bài

`GrantProgram` trả tiền theo voucher được committee ký. Mục tiêu là làm số dư xuống dưới 1% dự trữ để `isSolved()` trả `true`.

## Phân tích

Hai đường đổi voucher dùng chung chữ ký trên `(amount, nonce)`, nhưng thứ tự cập nhật trạng thái khác nhau:

| Selector | Đường xử lý | Thứ tự |
|---|---|---|
| `0x31d1299d` | Onboarding / `redeem` | Kiểm tra chữ ký → đánh dấu voucher đã dùng → chuyển ETH |
| `0x7c05469e` | `disburse` | Kiểm tra chữ ký → chuyển ETH → đánh dấu voucher đã dùng |

Cả hai có ABI `(address to, uint256 amount, uint256 nonce, bytes sig)`. Digest chỉ ràng buộc `(amount, nonce)`, không ràng buộc người nhận hay đường thực thi. Có thể dùng voucher onboarding với `disburse` và một contract nhận tiền có khả năng gọi lại.

## Lời giải

### 1. Xác định voucher và contract

Các giá trị của instance trong bản ghi:

- Setup: `0x66977ca8d525A4B51a851Cbda5d1fb44Bfb322aC`.
- GrantProgram: `0x40676c7618d9F9F62e02e6E67cD0c18b47EeE086`.
- Voucher: `amount = 1 ether`, `nonce = 0`.
- Digest: `keccak256(abi.encode(1 ether, 0))`, ký với Ethereum signed-message prefix.

### 2. Khai thác reentrancy

Trong `disburse`, ETH `CALL` ở pc `0x477`, còn lệnh ghi `voucherUsed[digest] = true` ở pc `0x503`. Khi contract nhận ETH được gọi, voucher vẫn chưa bị đánh dấu đã dùng.

`StandingOrderExploit` gọi `disburse(address(this), 1 ether, 0, sig)`. Hàm `receive()` gọi lại cùng selector, cùng voucher nếu chương trình còn ít nhất 1 ETH. Chuỗi 20 lần rút làm hết dự trữ 20 ETH trước khi các lời gọi quay về cập nhật trạng thái.

### 3. Kiểm tra điều kiện hoàn thành

Các giao dịch đã ghi lại:

- Deploy: `0xd4f2f26cb3c91efeeef62bd190fc44de3758112a986d1663117b380a2d6021d0`.
- Attack: `0x7c316486601a2b272de36e97fe352c4bf33a34af1625fdf9f6a7864b23fc3867`, dùng 374.966 gas.
- Kết quả: `GrantProgram.balance = 0`, `isSolved() = true`.

Ngưỡng kiểm tra là `RESERVE/100 = 0.2 ETH`; số dư 0 đáp ứng điều kiện này. Địa chỉ và chữ ký phải lấy lại theo instance khi tái hiện, không dùng các địa chỉ đã hết hạn như một mục tiêu đang hoạt động.

## Kết quả

```
hiCTF{one_sig_two_paths_then_the_l00p_a0f353c92e}
```
