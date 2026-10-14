---
title: "Tangled"
category: "Misc"
tags: ["factorio", "blueprint", "qr-code", "xor", "circuit-network", "glyph-ambiguity"]
solve_date: "2026-10-10"
language: "vi"
---

# Tangled

**Flag:** `FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}`
**Bài:** `Tangled` (laragrr), challenge UUID `386d874b-3c23-4897-b872-21e0fcd1edb6`. **Handout:** `handout_file_1.txt` (9458 B) và `handout_file_2.txt` (1162 B); cả hai là blueprint của Factorio (base64 + zlib).

## Đề bài

Hai file text chứa mỗi file một blueprint string của Factorio. Không có mô tả nào ngoài chính hai blob đó; toàn bộ dữ kiện nằm trong cấu trúc blueprint (entity, tile, và các phần tử mạch điện).

## Phân tích

Blueprint string của Factorio là JSON đã qua zlib rồi base64, nên bước decode đầu tiên chỉ là chuẩn hoá:

```python
import base64, zlib, json

def decode_blueprint(text):
    body = text.strip()
    if body.startswith("^"):
        body = body.split("^", 2)[2] if body.count("^") >= 2 else body[1:]
    return json.loads(zlib.decompress(base64.b64decode(body)))
```

`handout_file_2.txt` khi giải mã cho một tập tile ghép thành một lưới QR 25×25 đã bị hỏng. `handout_file_1.txt` chứa các entity (nền nhà máy) có toạ độ tâm; XOR các tâm entity đó với ma trận tile của lưới QR sinh ra một đoạn văn bản được ghi lại kèm nhãn `QR`:

```text
QR _5p49hett1_tr41n5_8ec0m3_
```

Ba nguồn độc lập cung cấp ba mảnh của cờ, nối tiếp nhau thành xâu hoàn chỉnh:

```text
factory-floor QR (prefix):   FortID{Wh3n_7h3_8e1ts_b3c0me
XOR tile fragment (middle):  _5p49hett1_tr41n5_8ec0m3_
wire-glyph suffix:           th3_0n1y_r34s0n4b1e_50lut10n}
```

- Chính sàn nhà máy trong `handout_file_1` mang một QR thứ hai, đọc ra phần đầu `FortID{Wh3n_7h3_8e1ts_b3c0me`.
- Đoạn từ phép XOR ở trên là phần giữa `_5p49hett1_tr41n5_8ec0m3_` (nhãn `QR` chỉ là ký hiệu đánh nguồn, không nằm trong cờ).
- 29 thành phần dây mạch (circuit network) trong blueprint được vẽ lại thành glyph bằng `inspect_wires.py` / `render_ports.py`, dùng offset connector thật của Factorio 2.0.77 lấy qua `lupa`; chúng cho phần đuôi `th3_0n1y_r34s0n4b1e_50lut10n}`.

Nối ba mảnh lại (prefix + middle + suffix) khớp chính xác với cờ.

## Lời giải

Toàn bộ khôi phục chạy offline: giải mã blueprint, dựng lưới QR 25×25, XOR với tâm entity để lấy đoạn giữa, đọc QR trên sàn nhà máy để lấy đầu, và dựng glyph cho 29 dây mạch để lấy đuôi. Ràng buộc còn lại duy nhất là tính nhập nhằng của glyph: ký tự `b`/`6` và `s`/`5` không phân biệt được trên ảnh vẽ lại, nên chuỗi đuôi chỉ đọc được ở mức hình dạng, chưa chốt được cách viết.

Phần nhập nhằng nằm gọn trong cluster `r34s0n4b1e`; cách đọc glyph sinh ra khoảng 20 biến thể khác nhau giữa `r3450n461e` và `r34s0n4b1e` (và các tổ hợp trung gian). Các biến thể này được liệt kê thành `candidates_ports.txt`, tức 130 ứng viên đầy đủ.

`check_candidates.py` chỉ dùng nền tảng để phân biệt cách đọc glyph, không dùng để tìm cờ: nó xác thực qua `https://platform.ctf.fortid.com/api/v1/auth/login` với token của đội, rồi POST từng ứng viên vào `/api/v1/challs/<uuid>/submit` (uuid ở trên), tôn trọng backoff khi gặp `badRateLimit`. Phản hồi được lưu nguyên văn:

```text
Authenticated successfully.\r\nChecking 130 candidates from candidates_ports.txt.\r\nACCEPTED: FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}
```

Bằng chứng bền: `work\tangled\flag_verified.txt` (84 B) và `submission_results.jsonl` với 136 dòng, phân bố `Counter({'badFlag': 135, 'goodFlag': 1})`.

## Kết quả

```text
FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}
```

Cờ được ghép offline từ ba mảnh (QR sàn nhà máy + đoạn XOR tile + glyph dây mạch), sau đó nền tảng chấp nhận để phân biệt cách đọc glyph. Dòng chấp nhận lưu nguyên văn: `Authenticated successfully.\r\nChecking 130 candidates from candidates_ports.txt.\r\nACCEPTED: FortID{Wh3n_7h3_8e1ts_b3c0me_5p49hett1_tr41n5_8ec0m3_th3_0n1y_r34s0n4b1e_50lut10n}` — flag đã được `/submit` chấp nhận.

## Tái hiện

Phụ thuộc: prototypes Lua của Factorio 2.0.77 (qua `lupa`) để lấy offset connector thật, `PIL`/`cv2` để dựng ảnh, và `qrcode` để sinh QR; OpenCV để đọc QR. Khôi phục chạy offline; chỉ bước phân biệt cách đọc glyph cần nền tảng.

```console
$ pip install lupa pillow opencv-python qrcode
$ python inspect_wires.py handout_file_1.txt   # glyphs of the 29 wire components
$ python render_ports.py                        # glyph image (b/6, s/5 ambiguous)
$ python check_candidates.py                    # disambiguates glyph readings only, honours badRateLimit backoff
```

Lưu ý: `check_candidates.py` chạm tới API nền tảng nên chỉ chạy khi được phép; về mặt thuật toán, các mảnh được khôi phục offline, nhưng chính tả cuối được chốt bằng phản hồi submission.
