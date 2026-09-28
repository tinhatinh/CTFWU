# notes.md — Owner's Draw (crypto / MAC length extension)

## H1 — định dạng chữ ký quyết định hướng tấn công
target: `GET /` + `GET /sample`
evidence: `X-Signature = SHA256(secret || body)` — hash của (secret prefix || message), không phải HMAC
result: CONFIRMED — đây là pattern Merkle–Damgård length extension. `/v2/webhook` dùng HMAC-SHA256 nên miễn nhiễm (đo trực tiếp: cùng chữ ký bị 401), và bài chỉ có 1 objective nên v2 là đối chứng, không phải nhánh bắt buộc.

## H2 — payload đích
evidence: body thật kết thúc bằng `&role=owner`? không, `&role=guest`; hint "an owner-role payout releases the flag"; server parse urlencoded và **lấy lần xuất hiện cuối** của khoá (giả thuyết, kiểm chứng bằng chính response)
did: suffix = `&role=owner`
result: CONFIRMED — response cuối là `{"ok": true, "payout": "authorized", ...}`

## H3 — brute force độ dài secret
evidence: padding phụ thuộc `len(secret)+len(body)` mà ta không biết len(secret); mỗi giả thuyết cho một (body, tag) khác nhau
did: thử s_len = 0..64, dùng chính server làm oracle (401 vs 200)
result: CONFIRMED tại **s_len = 15**. Bằng chứng chéo: 8 byte độ dài trong padding là `0x00000000000002d8` = 728 bit = 91 byte = 15 + 76 ✓ khớp độc lập với số lần thử.

## Chuỗi cuối
```
forged_body = body || 0x80 || 0x00*k || be64(8*(15+76)) || "&role=owner"
forged_sig  = SHA256_state_continue(tag, forged_body phần đuôi)
```
`python solve_draw.py` -> 200 + flag `H7CTF{786dff67-75cd-4d4e-8b74-55edb1353aad}`

## 5 lỗi đã gặp (tất cả đều ở code tự viết, không phải ở tín hiệu/data)
1. **Thiếu length field trong padding**: ban đầu `pad = 0x80 + 00*...` chỉ tới boundary 64 byte. Sai: digest công bố là state **sau cả block chứa độ dài**, nên phần splice phải gồm luôn `be64(bitlen gốc)`. Sửa: `pad = 0x80 + 00*((55-L)%64) + struct.pack(">Q", L*8)`.
2. **Self-test so sánh sai đối tượng**: so `forged` với `sha256(secret+body+suffix)` trong khi message thật server hash là `secret+body+pad+suffix`. Khiến code đúng cũng bị báo sai.
3. **Typo trong bảng K**: `K[19] = 0x240CA4CC`, giá trị chuẩn là `0x240CA1CC`. Tìm ra bằng cách tự sinh lại toàn bộ 64 hằng số từ `frac(cbrt(prime_i))` và diff từng phần tử.
4. **Sai dòng cập nhật state**: viết `hh,g,f,e,d,c,b,a = g,f,e,(d+t1),d,c,b,(t1+t2)` — ba vị trí cuối phải là `c,b,a` (tụt xuống), không phải `d,c,b` (giữ nguyên). Nghiêm trọng hơn: bản "reference" tôi viết tay để đối chiếu **mắc y cùng một lỗi**, nên hai bản khớp nhau mà vẫn khác hashlib. Kết luận: đừng lấy bộ não thứ hai của chính mình làm ground truth; chỉ chuẩn là `hashlib` trên message đầy đủ.
5. **Điều kiện lưu flag quá chặt**: bắt chuỗi `"owner"` trong khi response trả `"payout": "authorized"` -> có cờ trong tay nhưng không ghi `flag.txt`. Sửa: chỉ regex `H7CTF\{...\}` trên response.

## Vì sao phải viết SHA-256 thuần Python
`hashlib` không cho nạp lại trạng thái giữa dòng (không có API để "tiếp tục từ digest"), nên length extension cần tự cài `compress`. 64 vòng × 8 từ, chạy trong chưa tới 1 ms mỗi payload thử.
