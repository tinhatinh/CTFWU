---
title: "Soul Ascension"
category: "Mobile"
tags: ["android", "native", "xtea", "fnv-1a", "androguard", "ghidra-headless"]
solve_date: "2026-10-09"
language: "vi"
---

# Soul Ascension

**Flag:** `OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}`
**Artifact:** `SoulAscension.apk` (4978361 B) — `classes3.dex` (9052 B, ứng dụng) và `classes.dex` (7755924 B, AndroidX), cùng `lib/arm64-v8a/libguardian.so` (417456 B, stripped, build bằng NDK r27, xuất `Java_com_byteme_soulascension_MainActivity_nativeFinal` tại `0x27390`).

## Đề bài

Soul Ascension (Mobile, Hard, 300 điểm, tác giả Pratik Jadhav). Cờ nằm trong dữ liệu được mã hoá của native library, và khoá chỉ tái dựng được sau khi giải bốn guardian ở lớp Java.

## Phân tích

Lớp Java được đọc bằng androguard; `libguardian.so` được decompile bằng Ghidra headless.

Lớp Java — bốn guardian, mỗi con đóng góp một fragment của chuỗi khoá:

- `memory`: độ dài 6, điều kiện `mix(w) == 44689`.
- `moon`: lưu ngược (`noom`), suy ra `moon`.
- `soul`: `chr(c ^ 7) == "thrk"`.
- `2026`: `sum((d_i - 48) ^ (i + 3)) == 12`.

Ghép lại thành chuỗi:

```text
A9yromem:B4moon:C2tpvm:D82620
```

Lớp native — `libguardian.so` dùng XTEA với khoá dẫn xuất từ chuỗi trên, rồi kiểm kết quả bằng FNV-1a đối chiếu hằng số `0x757052CA`.

## Lời giải

Quét các biến thể chuỗi và thử từng model chain; model khớp vượt qua phép thử FNV-1a và giải mã CBC ra cờ:

```text
digit candidates: 326 ... [HIT] chain=A9yromem:B4moon:C2tpvm:D82620 cbc b'OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}'
raw plaintext: b'OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}\x01'
FLAG: OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian} len 39 FNV ok: True
```

Chuỗi khớp là `A9yromem:B4moon:C2tpvm:D82620`; plaintext CBC dài 39 byte đúng bằng độ dài cờ, `FNV ok: True`. Byte `\x01` cuối là padding.

## Kết quả

```text
OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}
```

Cờ được khôi phục tĩnh từ APK và khớp phép kiểm FNV-1a trong native library. Bài chưa kèm solver đầy đủ cho bước dẫn xuất khoá và XTEA-CBC; output trong bài là kết quả đã lưu.

## Tái hiện

Cần phân tích tĩnh `SoulAscension.apk`: androguard cho lớp Java, Ghidra headless cho `libguardian.so`. Lời giải giải mã khối CBC chứa trong native library bằng khoá XTEA dẫn xuất từ chuỗi `A9yromem:B4moon:C2tpvm:D82620`, kiểm FNV-1a với `0x757052CA`, không chạy APK.
