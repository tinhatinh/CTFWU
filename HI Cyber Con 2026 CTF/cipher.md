---
title: "Cipher"
category: "Mobile"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# Cipher

## Đề bài

Một APK Android chứa vault bị khóa bằng passphrase sáu từ. Mục tiêu là khôi phục passphrase, giải mã các bản ghi trong vault và tìm flag.

## Phân tích

Các lớp trong `classes*.dex` cho thấy ba thành phần chính:

- `CryptoEngine`: dùng PBKDF2-HMAC-SHA256 với 32.768 vòng và salt 16 byte từ `p7.bin` để suy ra root key. Mỗi bản ghi tiếp tục dùng HKDF-SHA256, salt riêng và info `"v1" + index` để lấy khóa AES-256-GCM; AAD là `"V1LT" + index`.
- `AnchorReader`: đọc verifier 16 byte từ `n3.bin`, một file 96 byte được giải XOR theo vị trí.
- `VaultStore`: parse magic `V1LT`, salt và 64 bản ghi trong `p7.bin`; mỗi bản ghi có index, nonce, ciphertext và tag.

Không cần tấn công trực tiếp AES. Package `legacy` tuy không được UI gọi tới nhưng vẫn chứa bộ sinh passphrase với không gian seed nhỏ.

## Lời giải

### 1. Thu hẹp seed

`SeedWindow.base()` trả `0x2d8c0000`, còn `span()` là `2^18`, tức 262.144 seed cần thử. `LegacyPassphrase.fromSeed()` dùng `java.util.Random(0x6a09e667f3bcc909 ^ seed)` để chọn sáu từ trong từ điển `m4.bin` đã che XOR, rồi thêm checksum hai chữ số.

Khi viết lại bộ sinh phải giữ đúng hành vi `Random.nextInt(100)`: đây là phép lấy modulo có rejection, không tương đương lấy các bit cao từ `nextInt(256)`.

### 2. Dùng verifier để chọn ứng viên

Duyệt cửa sổ seed và kiểm tra từng passphrase với HMAC verifier. Ứng viên khớp trong bản ghi là:

```
seed       = 0x2d8ff383
passphrase = smxvoisk-fcxfgnpl-poznukfv-zxpmztpo-yanlxwmm-yanlxwmm-42
```

### 3. Giải mã vault

Chạy chuỗi PBKDF2 → HKDF → AES-GCM trên 64 bản ghi bằng passphrase này. Bản ghi số 47, tiêu đề “Archived security memo”, chứa:

```
hiCTF{cryptography_should_be_implemnetd_properly}
```

## Kết quả

```
hiCTF{cryptography_should_be_implemnetd_properly}
```

Giữ nguyên lỗi chính tả `implemnetd` trong flag. Bản tóm tắt hiện có mô tả pipeline và giá trị tìm được; nó không kèm implementation đầy đủ của bộ giải mã `m4.bin`/`n3.bin` hay script brute-force để chạy độc lập với APK gốc.
