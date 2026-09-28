# Kintsugi Vault — Rev (Hard)

- Sự kiện: H7TEX 2026 (nền tảng WebVerse / ctf.h7tex.com)
- Thể loại: Rev (Docker), độ khó hard, 500 điểm
- Flag Format: `H7CTF{...}`
- Instance: `https://web-d6403eb95a65eea4.web.h7tex.com`
- Tệp đính kèm: `handout.tar.gz` (347257 byte, sha256 `4ce8375d99e0239992b6d2cb75a380cdf1c1747a94e9c06a1c81a9cc54e619c9`)

## Đề bài (nguyên văn)

> A retired key-custody vault shattered its root seed across a mesh of tiny guardian agents and lost
> the tool that glues them back. The re-attestation socket is still listening.
>
> Put the seed back together and prove it to the socket.

Objectives: 0/1 - `flag`.

## Nội dung handout

```
MANIFEST.txt
  Kintsugi Vault shard dump
  team: team-local
  chain start: f6f11ad133cab21c96e0185e3411ddc4
  shards are named by content id; order is not preserved on disk
  the start shard carries its decode table in the clear
  reassemble the 32 byte custody seed, then re-attest at the live endpoint

README.txt (tóm tắt)
  vault.json                 -> public verification key + endpoint
  guardian_<id>.bin (x7)     -> các mảnh guardian, mỗi file 1211 byte
  vmrun                      -> runtime để chạy thử một mảnh với 8 byte key ứng viên
  Usage: ./vmrun <shard-file> <16-hex-key> [decode-table-file]
  GET  /attest   -> {"nonce": "<48 hex>"}
  POST /attest   -> {"nonce": ..., "sig": "<hex>"}  -> {"flag": ...} khi sig hợp lệ
```

`vmrun` báo nhận/từ chối một key 8 byte cho từng mảnh; mảnh không phải đầu chuỗi còn cần
một "decode table" 256 byte truyền vào tham số thứ ba - chính cái "tool đã mất" mà ta phải tự viết lại.
