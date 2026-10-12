---
title: "SoulVault"
category: "Mobile"
tags: ["android", "jni", "radare2", "proof-of-work", "fnv-1a", "sha-256"]
solve_date: "2026-10-09"
language: "vi"
---

# SoulVault

**Flag:** `OWASP{soul_vault_fragment_recovered}`
**Artifact:** `SoulVault.apk` (1454312 B) — chứa duy nhất `classes2.dex`, `AndroidManifest.xml`, `res/layout/activity_main.xml` và `lib/{arm64-v8a,armeabi-v7a,x86,x86_64}/libsoulgate.so`.

## Đề bài

SoulVault (Mobile, Medium, 200 điểm, tác giả Pratik Jadhav): "Analyze the Android client and native proof-of-work flow to unlock the Soul Vault." Client gọi backend `https://byteme-soulvault-api.onrender.com`. Một bài khác cùng tên "SoulVault" nằm ở category Reverse Engineering (slug `soulvault-go`) và không liên quan tới bài này.

## Phân tích

Lớp Java được decompile bằng jadx CLI (`jadx.cli.JadxCLI`; launcher trên PATH mở GUI nên không dùng được cho batch). Từ đó thu được hai hàm native `SoulBridge.p` và `SoulBridge.q`, chuỗi thiết bị `MANUFACTURER:MODEL:SDK_INT` và base URL nói trên.

Lớp native `libsoulgate.so` phân tích bằng radare2 cho ra ba mảnh:

- Một blob 22 byte tại `.rodata:0x14d20`, XOR với key lặp `"Soul-Gate-917"`, trả về đường dẫn endpoint `/v1/soul/echo/fragment`.
- `p@0x26010` tính FNV-1a (offset basis `0x811c9dc5`, prime `0x1000193`), rồi `h ^= h >> 13`, `rotl(h, 7)`, `h ^ len*0x9e3779b9`, tiếp theo là một murmur finalizer; kết quả được định dạng `g3-%08x`. Đây chính là client token.
- `q@0x26420 → 0x266c0` là một chuỗi SHA-256 gồm 4 vòng; điều kiện chấp nhận là đầu ra có `difficulty` bit 0 dẫn đầu. Đây là vòng lặp proof-of-work.

## Lời giải

Luồng mở khoá: `GET` endpoint để lấy `difficulty`, `nonce`, `ticket`; dựng client token `g3-…` bằng `p`; sau đó chạy `q` trên seed có thành phần đầu tiên là client token, tăng bộ đếm cho tới khi tổng SHA-256 đủ số bit 0 dẫn đầu theo `difficulty`, rồi `POST` bằng chứng. Chạy solver `python -u solve.py "Google:Pixel 7:33"` (lưu trong `soulvault/run1.txt`):

```console
$ python -u solve.py "Google:Pixel 7:33"
```

```text
GET 200 {"difficulty":20,"nonce":"7745e72075f3b08185931a912d3fc6c0","ticket":"b44856ea67b3388b463deece16834892"}
counter = 1783227  (10.0s, sha256 zero-bits=22)
POST 200 {"fragment_id":"2e76740874975b60","message":"OWASP{soul_vault_fragment_recovered}","status":"awakened"}
```

Chuỗi thiết bị khớp với phép kiểm phía client:

```text
sha256("Google:Pixel 7:33") = 0e71c95267c1f813a5870d5bff97f1aaf2ab3439fc52fa98f4ccd7a676a9b9ab
```

`POST 200` trả về `message` chứa cờ. Run được tái hiện lần thứ hai từ một thiết bị/client khác, trả về `fragment_id 23c5aa7f88e9ef6a` với cùng `message`.

## Kết quả

```text
OWASP{soul_vault_fragment_recovered}
```

Cờ đọc trực tiếp từ dịch vụ: `POST /v1/soul/echo/fragment` trả về `message` chứa flag, và kết quả tái hiện được ở client thứ hai. Chưa lưu phản hồi submission.

## Tái hiện

Cần API còn hoạt động. Solver đã lưu mô phỏng token `p` và proof-of-work `q`; bài chưa kèm mã solver hay chi tiết đầy đủ của seed và bốn vòng SHA-256, nên các bước trên mới là mô tả luồng cùng output đã ghi nhận.
