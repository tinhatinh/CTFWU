# Eat your fruits and vegetables! - Crypto (500 points)

**Flag:** `cdctf{Carrot}` · **Files:** `data.db.enc`, 960000 byte, sha256 `ea8bfa7cfc6f9f319ccf4f5efa12377beb84087ffb5885bd975656cc628e0374`

## Đề bài

Một cơ sở dữ liệu đã bị đánh cắp và mã hoá bằng AES-128 trong chế độ ECB, cho sẵn dưới dạng `data.db.enc`. Sau khi giải mã, mỗi người chiếm đúng 32 byte: 8 byte tên, 8 byte hãng xe, 8 byte loại hoa quả yêu thích, 8 byte hệ điều hành, tất cả padded bằng null. Đề cho bảng phân bố của từng trường và nói rằng mọi người tên Bob đều thích cùng một loại hoa quả. Nhiệm vụ là tìm loại hoa quả đó; cờ có dạng `cdctf{Produce_Item}` và chỉ được nộp hai lần.

Không có key và không có oracle giải mã, nên toàn bộ thông tin phải lấy từ chính ciphertext.

## Phân tích

File dài 960000 byte, chia hết cho 16 và 32. Đề đã xác định AES-ECB; phân tích dưới đây dùng số lượng và tần suất các block lặp để khôi phục thông tin thống kê, không suy ra chế độ mã hóa từ entropy.

Cắt file theo block 16 byte và đếm giá trị phân biệt:

```python
>>> d = open('files/data.db.enc', 'rb').read()
>>> len(set(d[i:i+16] for i in range(0, len(d), 16)))
54
```

60000 block ciphertext chỉ có 54 giá trị khác nhau. ECB ánh xạ khối plaintext tới khối ciphertext một cách đơn trị, nên khối giống nhau cho ciphertext giống nhau: toàn bộ không gian giá trị của các trường đã lộ ra ngoài mà không cần giải mã. 54 = 36 + 18 đúng bằng `12 tên x 3 hãng xe` ở nửa đầu record và `6 loại hoa quả x 3 hệ điều hành` ở nửa sau, xác nhận cách cắt 32 byte là đúng.

Gọi `A` là block "tên + xe", `B` là block "hoa quả + OS". Vấn đề quy về việc tìm ba block `A` thuộc về Bob rồi đọc `B` đi kèm.

## Hướng đã thử

Trước khi chốt đã kiểm tra và loại các kênh sau (log đầy đủ ở `notes.md`):

1. **Tấn công AES để lấy key**: ciphertext-only, không có oracle, độ an toàn của bản thân AES không phải thứ bị phá ở đây.
2. **Chọn block `A` theo tần suất để nhận diện Bob**: 36 block `A` có tần suất từ 786 đến 872, sát quanh giá trị kỳ vọng 30000/36 = 833, không có block nào khác biệt.
3. **Dùng con số "Bob - 5%" trong đề**: nhóm bị ràng buộc thật sự chứa đúng 2500 dòng, tức 1/12 chứ không phải 5%. Tỉ lệ tên trong đề không khớp dữ liệu quan sát; bảng hoa quả mới khớp dữ liệu.
4. **So 8 byte đầu của các block `B` với nhau**: ECB mã hoá trọn block 16 byte, hai plaintext chỉ khác nửa sau vẫn cho ciphertext khác hoàn toàn. Ba block `B` của cùng một loại hoa quả không có chung byte nào.

## Lời giải

**Bước 1 - Đếm block theo vị trí trong record.** Với mỗi record 32 byte, lấy `A = record[0:16]` và `B = record[16:32]`, dựng hai bảng tần suất và bảng tần suất của cặp `(A, B)`. Kết quả: 36 block `A` phân biệt, 18 block `B` phân biệt.

**Bước 2 - Gom các block `A` theo tập hợp block `B` đứng ngay sau nó.** Với tên không bị ràng buộc, hoa quả độc lập với tên và xe, nên mọi block `A` của tên đó phải xuất hiện cùng đủ 18 block `B`. 33 trong số 36 block `A` rơi vào đúng một nhóm như vậy. Nhóm còn lại là của Bob: ba block `A` (ba hãng xe) chỉ xuất hiện cùng ba block `B`, và ba block `B` đó phủ đúng 2500 dòng.

```python
from collections import Counter, defaultdict
d = open('files/data.db.enc', 'rb').read()
B, follow = Counter(), defaultdict(Counter)
for i in range(0, len(d), 32):
    a, b = d[i:i+16], d[i+16:i+32]
    B[b] += 1; follow[a][b] += 1

groups = defaultdict(list)
for a in follow:
    groups[frozenset(follow[a])].append(a)

for bset, alist in groups.items():
    if len(bset) < len(B):                     # tap B hong bo
        rows = sum(sum(follow[a][b] for b in bset) for a in alist)
        print(len(alist), len(bset), rows)
```

```
3 3 2500
```

3 block `A` x 3 block `B` x 2500 dòng là cấu trúc duy nhất trong toàn bộ dữ liệu: một tên có hoa quả cố định, vẫn chia đều cho ba hãng xe và ba hệ điều hành.

**Bước 3 - Đọc loại hoa quả từ tổng tần suất toàn cục.** Bên trong nhóm Bob, ba block `B` gần như bằng nhau (885/805/810 dòng) nên không phân biệt được gì; thông tin nằm ở chỗ ba block ấy thuộc về loại hoa quả nào trong toàn bộ 30000 dòng. Vì cả ba là cùng một loại hoa quả với ba hệ điều hành khác nhau, tổng tần suất của chúng trên cả cơ sở dữ liệu chính là phần trăm của loại hoa quả đó:

```
1852 + 1780 + 1768 = 5400 dong = 18,00% cua 30000
```

Đối chiếu bảng của đề: Apple 10% = 3000, Orange 12% = 3600, Banana 15% = 4500, Carrot 18% = 5400, Onion 21% = 6300, Potato 24% = 7200. Giá trị 18% ánh xạ duy nhất vào Carrot.

**Bước 4 - Kiểm chứng.** Sắp 18 block `B` theo tần suất giảm dần và tách cụm theo khoảng cách:

```
      3 block, tong 7200 dong = 24.00% -> Potato
      3 block, tong 6300 dong = 21.00% -> Onion
      3 block, tong 5400 dong = 18.00% -> Carrot
      3 block, tong 4500 dong = 15.00% -> Banana
      3 block, tong 3600 dong = 12.00% -> Orange
      3 block, tong 3000 dong = 10.00% -> Apple
```

18 block tách đúng thành 6 cụm 3 block, tổng các cụm khớp chính xác từng dòng với bảng phân bố của đề, kể cả tỉ lệ 33.33% của hệ điều hành bên trong mỗi cụm. Ba block của nhóm Bob nằm gọn trong cụm 18%: chúng có cùng một loại hoa quả thật, phù hợp với ràng buộc Bob chỉ thích một loại hoa quả.

## Kết quả

```bash
python exploit.py files/data.db.enc
```

```
[*] data.db.enc: 960000 bytes = 30000 record 32 byte
[*] block loai A (ten+xe) phan biet: 36 (ky vong 36)
[*] block loai B (hoa qua+OS) phan biet: 18 (ky vong 18)
[*] gom B-block theo khoang cach tan suat:
      3 block, tong 7200 dong = 24.00% -> Potato
      3 block, tong 6300 dong = 21.00% -> Onion
      3 block, tong 5400 dong = 18.00% -> Carrot
      3 block, tong 4500 dong = 15.00% -> Banana
      3 block, tong 3600 dong = 12.00% -> Orange
      3 block, tong 3000 dong = 10.00% -> Apple
[*] nhom A-block co tap B hong bo: 1
      3 A-block (= 3 xe cua cung mot ten), 3 B-block, 2500 dong
      483a10eb3d9fb3e96542da3c5348b7ae  tong 1852  trong nhom 885
      7ad7bda141552326c6ac06ac5ef29b0c  tong 1780  trong nhom 805
      30cbb1d20626d60fae57c430ec450bbf  tong 1768  trong nhom 810
[+] 3 B-block cua nhom nay chiem 5400/30000 dong = 18.00% -> Carrot
[+] flag: cdctf{Carrot}
```

## Tái hiện

```bash
python exploit.py files/data.db.enc
# Dau ra mong doi: [+] flag: cdctf{Carrot}, ma thoat 0, flag.txt duoc ghi
```

Script chỉ dùng stdlib, kiểm tra độ dài file, số block phân biệt, độ lớn 3x3 của nhóm ràng buộc và tính khớp của cả sáu cụm tần suất; nếu bất kỳ điều kiện nào sai thì thoát với mã lỗi thay vì in cờ.
