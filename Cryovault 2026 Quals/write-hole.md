---
title: "Write Hole"
category: "Forensics"
tags: ["raid5", "recovery"]
solve_date: "2026-10-10T11:41:00+07:00"
language: "vi"
---

# Write Hole

**Flag:** `isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}`  
**Artifact:** `bay0.img`, `bay1.img`, `bay2.img` (17,825,792 bytes each)
| Artifact | SHA-256 |
|---|---|
| `bay0.img` | `38226d020b3cfc46f587dae721df0ed61d9886e36043abaa0d3071c3635258a6` |
| `bay1.img` | `18b526944cc99801152c49724cb03cbdb4ab6eeb566f0c82c8b60fe802c21860` |
| `bay2.img` | `2e6ee1100f9bb2d68a85f85e6992d0f0eb6cfe5df3e487c4fba8c0b004d455d0` |

## Đề bài

Khôi phục encrypted report và custody token từ ba disk image NAS bị mất điện lúc ghi. RAID configuration không được lưu.

## Phân tích

Ba image có cùng kích thước. Strings cho thấy ext4, sealing script và intent của job 7. Report gồm sáu record AES-GCM 32 KiB, mỗi record có SHA-256 trong intent. Keyslot đã xóa còn trong raw remnants: chọn record KSLT có CRC đúng và key digest khớp intent.

## Lời giải

1. Tìm ext4 superblock với member offset 1 MiB. Đối chiếu filesystem metadata/directory để xác định RAID-5 ba disk, chunk 32 KiB, left-symmetric parity.
2. Khôi phục `/stage/job-0007.intent`, payload, keyslot và notes. Dùng member data hoặc XOR hai chunk còn lại; chỉ giữ candidate khớp intent SHA-256.
3. Record có nonce 12 byte, ciphertext, tag 16 byte. Decrypt với job 7 key và AAD `payload.bin|7|<index>`.
4. Record 3 từ parity reconstruction lệch một bit. Prefix custody-token giúp định vị; XOR 0x02 tại offset 8876 của sealed record. Sau sửa, cả intent digest và GCM tag đều khớp.
5. Lấy ba shard từ plaintext authenticated theo số thứ tự 1,2,3 rồi nối thành flag. Các shard được giữ nguyên dưới đây.

## Kết quả

Flag được khôi phục từ disk image; cả sáu record được đối chiếu intent hash và GCM tag.

`isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}`

## Tái hiện

Dùng member offset 1 MiB, chunk 32 KiB, layout RAID-5 left-symmetric. Khôi phục key từ KSLT có CRC đúng và `SHA256(key)[:16]` khớp key_id. Với từng record, thử member/XOR candidate theo intent, sửa bit record 3 trước kiểm tra digest/tag, rồi lấy shard đúng thứ tự. Bản nguồn cung cấp thuật toán và checkpoint nhưng không kèm reconstruction script đầy đủ.

```text
All six record hashes and AES-GCM tags verified.
FLAG isfcr{p4r1ty_n3v3r_l13s_wr1t3_h0l3_r3m3mb3rs}
```
