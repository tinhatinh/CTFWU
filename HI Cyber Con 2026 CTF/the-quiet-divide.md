---
title: "The Quiet Divide"
category: "NTA"
tags: []
solve_date: "2026-10-31"
language: "vi"
---

# The Quiet Divide

## Đề bài

PCAP của Asterion Dynamics ghi lại hoạt động sau một đợt bảo trì. Hai domain `fleet-prod` và `dr-ops` đưa ra các chuỗi chứng cứ khác nhau. Cần xác định chuỗi production có thẩm quyền, khôi phục dữ liệu qua QUIC và archive rồi giải mã final seal.

## Phân tích

Policy quy định recovery không được finalize production. Do đó một nhánh giải mã được chưa đủ để coi là đáp án: checkpoint, commit, chữ ký và receipt phải cùng ràng buộc vào production case.

## Lời giải

### 1. Trích chứng cứ production đã ký

Từ HTTP JSON trong capture, lấy:

- Committee records `C0`–`C4`, threshold 3.
- Checkpoint `W0` có `terminal_event=b34dc728...`, `checkpoint_sha256=5e4f78ad...`.
- Năm custody record theo chuỗi `ROOT → PREP → COMMIT → PREP → COMMIT`, chữ ký 3-of-3 hợp lệ.
- Seal `mb-final-seal/10` chứa `archive_salt_hex`, `salt_hex`, `nonce_hex`, `ciphertext_b64`.

### 2. Khôi phục QUIC key log

XOR hai escrow share slot A và slot B lấy từ `/v3/escrow`, định dạng `mb-diagnostic-share/3`. SHA-256 của kết quả khớp `keylog_sha256`. Dùng key log để giải mã QUIC, thu observation `mb-quic-observation/3` được `ARCH-14` ký.

### 3. Dựng chuỗi evidence theo SDK

Chuỗi vật liệu được tính lần lượt từ:

1. `chain = SHA256(canonical(custody_events))`.
2. HMAC trên firmware `pulse-codec 7.7.0`, ghép từ bốn HTTP Range response; hash ghi trong bản lưu là `0835dfce...`.
3. Chữ ký attestation.
4. Chữ ký QUIC observation.
5. State digest `PulseWire` lấy từ frame `PLS2` của `/v2/frames`.

Canonicalization phải theo SDK, vì thay đổi cách serialize cũng thay đổi các digest và khóa tiếp theo.

### 4. Chọn archive có thẩm quyền

HKDF với `archive_salt_hex=6d562eb7...` suy ra khóa AES-GCM. Ba ứng viên `ops-17` giải mã thành SQLite chứa các bảng `transfers`, `receipts`, `fragments`, `operations`.

Ứng viên đúng là transaction `6dd9ec588c9914ca95df44b2` trong archive `5a2c8adef3c0846a2d0fb62d00844c64`, thỏa cả ba đối chiếu:

- `release_checkpoint = 5e4f78ad...`, đúng checkpoint được W0 chứng kiến.
- `case_commit = b34dc728...`.
- Receipt là `accepted`, fragment commit khớp vật liệu tính cục bộ.

### 5. Giải final seal

Dùng HMAC-SHA256 và codec digest để bỏ mask của bốn fragment, thu `material`. Khóa cuối được suy ra theo:

```
final_key = HKDF(material || evidence || witness_signature,
                 salt = ded3d12c..., info = "MIRRORBREAK/10/PRODUCTION-CASE")
```

Giải `ciphertext_b64` với nonce `0de2e11f...`, dùng các trường seal được canonicalize làm AAD. Nhánh recovery `dr-ops`, QUIC 4434 và escrow batch `fe3785...` là mồi nhử: policy không cho nhánh này finalize production.

## Kết quả

```
hiCTF{c8c46fdbd6e5e4eacabfba53a156ff9ab10567f2}
```

Các hash, salt và nonce có dấu `...` là giá trị rút gọn trong bản lưu, không phải input chạy được. Cần PCAP, SDK và đầy đủ các trường gốc để tái hiện pipeline; không thể dùng trực tiếp các prefix ở trên để giải mã.
