# Loose Lips — Crypto (Hard)

**Cờ v1:** `H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}`
**Cờ v2:** `H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}`
**File cung cấp:** `ckks.py` (Kịch bản 2272 B, sha256 `f905e01981fc8049…`)
**Máy chủ mục tiêu:** `https://web-550a48e366fd77e3.web.h7tex.com`

## Đề bài

Trò chơi đưa ta vào hệ thống tính toán thống kê "DecryptoStat" — một công cụ hùng hồn rêu rao rằng "nó không bao giờ dòm ngó được vào dữ liệu nguyên bản của bạn". Nền tảng này ứng dụng một phiên bản thu nhỏ của cơ chế mã hóa đồng cấu CKKS.
Hệ thống cung cấp hai cổng dịch vụ chạy song hành: một bản nguyên thủy (v1) và một bản "được tôi luyện lại" (hardened rewrite - v2). Mục tiêu khắc nghiệt: người chơi phải tước đoạt (recover) được khoá bí mật (secret key) của cả hai hệ thống, nộp những con số đó vào cổng `/v1/recover` và `/v2/recover` để lĩnh thưởng cờ.

## Phân tích ban đầu

Đẩy lệnh GET vào đường dẫn `/`, máy chủ ói ra một bảng thông số kỹ thuật liệt kê các hàm API kèm theo cấu hình mạng tinh thể (hệ mật): `N=8`, `Q=2^40-87`, độ nhiễu `DELTA=2^25`. Đắt giá nhất là dòng ghi chú vô tình làm lộ tử huyệt của hệ thống: *khoá bí mật là một vector bậc 3 (ternary vector) có độ dài chỉ 8 phần tử*.

Mổ xẻ file lõi `ckks.py`:

```python
def small(bound=1): return [secrets.randbelow(2*bound+1) - bound for _ in range(N)]
def keygen(): return small(1)                    # Bản chất: mỗi hệ số trong khoá chỉ được phép loanh quanh ở 3 giá trị -1, 0, hoặc +1
def encrypt(values, s):
    m = encode(values); a = rand_poly(); e = small(3)
    b = ring_add(ring_sub([0]*N, ring_mul(a, s)), ring_add(m, e))   # Thu gọn công thức: b = -a*s + m + e
    return b, a
def decrypt(ct, s, smudge=0):
    d = ring_add(b, ring_mul(a, s))              # Giải ngược: d = b + a*s = m + e
    if smudge: d = ring_add(d, small(smudge))    # Lớp khiên của bản v2: trò "noise flooding" (Bơm ngập nhiễu)
    return decode(d)
```

Ba luồng thông tin trên quy tụ lại thành một bức tranh giải pháp rực rỡ:

1. Kích thước không gian khoá (Keyspace) chỉ bằng `3^8 = 6561` khả năng. Con số này là mồi ngon, đủ nhỏ để máy tính cày nát (vét cạn) chỉ trong vài giây.
2. Cổng `POST /vN/encrypt` cho phép ta tự do ném vào bản rõ (plaintext) tuỳ ý, và máy chủ ngoan ngoãn nôn trả một cặp mã (b, a).
3. Sai số nhiễu được cấu hình `e = small(3)`, tức là mọi hệ số của đa thức dư `b + a*s - m` bị đóng khung trong biên độ từ [-3 đến 3]. Trong khi đó, quy mô gốc của một ciphertext lại phình to tận mức ~Q = 2^40. Phép so sánh này lệch pha hàng nghìn tỉ lần, biến giới hạn nhiễu trở thành một cỗ máy phát hiện khoá (test) chuẩn xác tuyệt đối.

Một đoạn ghi chú nhỏ ở đầu file `ckks.py` tiết lộ ranh mãnh: *"Lỗ hổng không nằm ở cấu trúc mã này; lỗ hổng nằm ở việc service trả về kết quả giải mã mang tính xấp xỉ (chứa nhiễu)"*. Đây rõ ràng là cái bẫy dẫn dụ người chơi tấn công qua lỗ hổng Decryption Oracle (đó cũng là lý do vì sao bản v2 cố tình tống thêm đống nhiễu `smudge` vào hàm decrypt để phòng chống). Vứt bỏ con đường đó đi, ta có cách đi thẳng hiệu quả hơn nhiều.

## Chuỗi khai thác

### Bước 1: Xin một bản mã (ciphertext) có giá trị 0 tròn trĩnh

Ép mảng `values = [0,0,0,0]`, khi qua khâu mã hoá, biến `m = encode(0)` sẽ triệt tiêu về 0. Lợi ích là phương trình cồng kềnh `b + a*s - m = e` sẽ co cụm lại chỉ còn `b + a*s = e` (với e mang giá trị cực nhỏ).

```python
c1 = post("/v1/encrypt", {"values": [0,0,0,0]})     # Trả về -> id, b, a
```

### Bước 2: Vét sạch toàn bộ không gian khoá Ternary (3 trạng thái), lọc cặn bã

```python
m = ckks.encode(values)
# Vòng lặp cày 6561 trường hợp của khoá
for s in itertools.product((-1,0,1), repeat=8):
    d   = ckks.ring_add(c1["b"], ckks.ring_mul(c1["a"], list(s)))
    res = ckks.ring_sub(d, m)
    # Nếu giới hạn nhiễu nhỏ hơn 3, tóm ngay khoá đó làm ứng cử viên
    if max(abs(int(x.real)) for x in ckks._center(res)) <= 3:
        cand.append(list(s))
```

Bí quyết để không bị lệch pha toán học (làm rớt mất khoá xịn) là ta lôi thẳng tệp `ckks.py` do tác giả cấp, nhúng (import) trực tiếp vào script bẻ khoá (`sys.path.insert(0,"files"); import ckks`). Nhờ thế, các phép toán `ring_mul`, `encode`, `_center` của ta sẽ rập khuôn y đúc 100% cơ chế xử lý bên phía máy chủ.

Kết quả đáng kinh ngạc: Chỉ nhờ đúng MỘT cặp ciphertext duy nhất, lưới lùng sục đã gạn lọc được chính xác một ứng cử viên độc tôn cho cả hai phiên bản, hoàn toàn không cần cày thêm các vòng phân loại phụ:

```text
=== Phiên bản v1 ===
[*] Khóa ternary khớp với bản mã 0-plaintext: 1 biến thể -> [[1, -1, 0, -1, 1, 1, -1, -1]]
=== Phiên bản v2 ===
[*] Khóa ternary khớp với bản mã 0-plaintext: 1 biến thể -> [[1, 0, 0, -1, -1, -1, 0, 1]]
```

### Bước 3: Đóng dấu kiểm chứng và ép máy chủ nhả cờ

Làm nốt một phép thử cho chắc cú: Yêu cầu mã hoá một chuỗi số dị biệt `values=[1.5, -2.25, 0.5, 3.0]`, sau đó dùng chính chiếc khoá vừa đoạt được để tự giải mã (decrypt) trên máy cá nhân:

```text
Log giải mã của v1: Giải về = [1.500000, -2.250000, 0.500000, 3.000000] (Sai số đỉnh max|err| chỉ = 1.952e-07)
    Đa thức nhiễu định tâm (noise poly centred) = [ 2, -3, -3, 0, -3, 2,  1, -2] (Nằm ngoan ngoãn trong quỹ đạo cho phép small(3))
Log giải mã của v2: Sai số đỉnh max|err| = 1.836e-07
    Đa thức nhiễu định tâm (noise poly centred) = [ 0,  3,  2,-2,  3,-2,  1, -2]
```

Bằng chứng rành rành: Mỗi cổng dịch vụ sử dụng một con khoá bị dính chết (cố định) qua hàng loạt request, và chiếc khoá trong tay ta giải mã hoàn hảo những gì máy chủ nôn ra.

Ném thành phẩm lên cổng `POST /v1/recover` và `POST /v2/recover`:

```json
{"ok": true, "flag": "H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}"}
{"ok": true, "flag": "H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}"}
```

### Chốt hạ: Chiêu "bơm ngập nhiễu" (hardened) vì sao trở nên phế vật ở bản v2?

Trò chơi bơm nhiễu `smudge` chỉ được cài cắm bên trong nhánh mã giải ngược `decrypt`: Mục đích của nó là trát bùn che mắt kết quả của oracle, cản trở bạn đi lùi để tính ngược ra `s` từ các lệnh gọi `/v2/decrypt`. 
Nhưng đường lối tấn công mà ta xây dựng hoàn toàn tẩy chay cái trò vặt đó: Ta chặn đầu rút cặp mã `(b, a)` từ chính cổng tạo mã `/v2/encrypt`, sau đó tự mở lò giải toán phân tích nghiệm tuyệt đối ngay trên phần cứng của mình. 
Hài hước thay, số liệu kiểm tra cho thấy một bản ciphertext khi vứt qua `/v2/decrypt` chỉ gây ra sai số 2.94e-07, xấp xỉ mức 1.95e-07 của v1. Điều đó phơi bày một sự thật: đống bùn (flooding) tác giả tống vào chả có tác dụng gì trên hướng đi này; và dù đống bùn đó có dày cỡ nào, nó cũng chả liên quan gì tới cái móng kiến trúc (primitive) mà ta bẻ gãy.

## Flag
```text
Cổng v1  H7CTF{08a5c5eb-7571-4a3d-a80d-599ddd46c5ad}   (Bằng con khoá: [1,-1,0,-1,1,1,-1,-1])
Cổng v2  H7CTF{89c0e6b2-9fca-49fd-a02f-07a70e359363}   (Bằng con khoá: [1, 0, 0,-1,-1,-1, 0, 1])
```

Dùng kịch bản hốt cờ: `python solve_lips.py` (Lệnh này rinh về cả 2 cờ, dán cẩn thận vào file `flags.txt`).
