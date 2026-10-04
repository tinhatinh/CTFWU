# Gerry the Larry (1/2) - Log Analysis (500 điểm)

**Cờ:** `cdctf{12}`
**File đính kèm:** `catcounty_results.zip` (37.241 B, SHA256 `462c4d84…5a9cb4`), bên trong là `gerry_final_files/{info.csv, check_in.log, votes.log}`
**Tác giả:** adlee7, reep236 (CDCTF)

## Đề bài

Ba file nhật ký bầu cử của Cat County do một công chức rò rỉ: `info.csv` liệt kê 1067 cử tri
với `id`, tên và block (đơn vị bầu cử) đang sống; `check_in.log` ghi lại 1067 lượt điểm danh tại
tổ bầu cử; `votes.log` ghi 1067 phiếu bầu cho một trong bốn đảng. Câu hỏi: Meowjority đang kiểm
soát bao nhiêu block, và đó là những block nào (danh sách cần cho phần 2). Cờ chỉ chứa con số,
định dạng `cdctf{##}`.

## Phân tích ban đầu

Định dạng ba file như sau (dòng đầu và dòng cuối của mỗi file):

```text
info.csv      31752947660,Luna,Midnight Zoomies Mile
              1067 dong moi, 36 gia tri block khac nhau
check_in.log  2026-10-01 07:45:27 550408395 11835863810
              2026-10-01 17:46:32 550409461 47281930635
votes.log     2026-10-01 08:00:45:381009204091:Nap Rights
              2026-10-01 17:59:50:381009205157:Meowjority
```

`voter_id` 11 chữ số trong `check_in.log` khớp toàn bộ với `info.csv` (1067/1067, không id nào
thừa, không id nào lặp), nên hướng block của từng lượt điểm danh xác định được ngay. Vấn đề còn
lại nằm ở `votes.log`: phiếu chỉ có số thứ tự ballot và tên đảng. Receipt trong `check_in.log` là
dãy 9 chữ số 550408395..550409461, ballot trong `votes.log` là dãy 12 chữ số 381009204091..381009205157,
giao nhau rỗng, tức hai log không chia sẻ khoá.

Hai log tăng theo thời gian, số thứ tự tăng 1 mỗi dòng và cùng có 1067 dòng. Lời giải giả định cử tri bỏ phiếu theo thứ tự check-in (FIFO), rồi ghép dòng i với dòng i. Khoảng cách thời gian 560..1184 s, trung bình 869 s, phù hợp với giả định này nhưng không tự chứng minh thứ tự bỏ phiếu.

## Các hướng đã loại

1. **Nối hai log bằng số thứ tự**: `set(receipt) & set(ballot)` rỗng vì hai dãy đánh số độc lập.
2. **Dịch pha một dòng** (phiếu i thuộc điểm danh i-1 hoặc i+1): hai cách này chỉ ghép được 1066 cặp,
   để thừa một lượt điểm danh và một phiếu không có đôi, trái với dữ kiện mỗi cử tri điểm danh đúng
   một lần và hai log dài bằng nhau. Kết quả cũng khác (10 và 9 block, xem `analysis/sensitivity.py`),
   nên đây là bước phải chốt trước khi tin con số 12.
3. **Đếm theo đa số tuyệt đối** (phải trên 50% số phiếu của block): được 9 block, tức giảm ba block so
   với plurality (Scratching Post Street 11/32, Tuna Terrace 11/25, Windowsill Way 6/20). Đề không nêu
   thể lệ count nào, nhưng không block nào hoà phiếu và cách tính "nhiều phiếu nhất thì giành block"
   được dùng làm giả định tính kết quả theo plurality.

## Chuỗi khai thác

**Bước 1 - Khôi phục quan hệ giữa phiếu và cử tri.** Vì hai log không có khoá chung, ghép theo thứ tự FIFO giả định, đồng thời in ra khoảng cách thời gian để thấy phép gán đó hợp lệ:

```text
[*] check_in : n=1067  don dieu thoi gian=True  so thu tu lien tiep=True  (550408395..550409461)
[*] votes    : n=1067  don dieu thoi gian=True  so thu tu lien tiep=True  (381009204091..381009205157)
[*] cua so mo cua: check_in 07:45:27..17:46:32, votes 08:00:45..17:59:50

[*] do lech (vote[i] - check_in[i+lag]) theo tung cach phoi:
     lag cap hop le    min    mean    max   am
      -2       1065    628   937.0   1252    0
      -1       1066    599   903.2   1216    0
      +0       1067    560   869.4   1184    0
      +1       1066    522   835.6   1160    0
      +2       1065    491   801.9   1128    0
```

Chỉ lag 0 dùng được vì nó là lag duy nhất phủ hết 1067 dòng của cả hai file; lag ±1 bỏ sót một đối
tượng ở mỗi đầu, còn lag ±2 bỏ sót hai.

**Bước 2 - Cộng phiếu theo block và phân định block.** Gán phiếu cho block qua `voter_id`, rồi lấy
đảng nhiều phiếu nhất trong block:

```python
tally = collections.defaultdict(collections.Counter)
for (_, _, voter), (_, _, party) in zip(checkin, votes):
    tally[voter_block[voter]][party] += 1

meow = [b for b in sorted(tally) if tally[b]["Meowjority"] == max(tally[b].values())]
```

```text
    Cardboard Court          n= 34  Meowjority:21  Tuna Reform:6  Nap Rights:4  Domestic Loafs:3  <== Meowjority
    Catnip Corner            n= 23  Meowjority:12  Domestic Loafs:5  Nap Rights:3  Tuna Reform:3  <== Meowjority
    Hairball Heights         n= 34  Meowjority:21  Tuna Reform:6  Nap Rights:4  Domestic Loafs:3  <== Meowjority
    Mousetrap Alley          n= 23  Meowjority:14  Tuna Reform:5  Nap Rights:4  <== Meowjority
    Pawprint Plaza           n= 31  Meowjority:16  Tuna Reform:9  Domestic Loafs:4  Nap Rights:2  <== Meowjority
    Purrington Place         n= 35  Meowjority:19  Tuna Reform:8  Domestic Loafs:6  Nap Rights:2  <== Meowjority
    Scratching Post Street   n= 32  Meowjority:11  Domestic Loafs:9  Tuna Reform:8  Nap Rights:4  <== Meowjority
    Sunbeam Square           n= 24  Meowjority:16  Domestic Loafs:4  Nap Rights:2  Tuna Reform:2  <== Meowjority
    Tuna Terrace             n= 25  Meowjority:11  Nap Rights:5  Tuna Reform:5  Domestic Loafs:4  <== Meowjority
    Whisker Row              n= 25  Meowjority:13  Nap Rights:8  Tuna Reform:3  Domestic Loafs:1  <== Meowjority
    Windowsill Way           n= 20  Meowjority:6  Tuna Reform:5  Nap Rights:5  Domestic Loafs:4  <== Meowjority
    Yarnball Yard            n= 25  Meowjority:14  Tuna Reform:5  Domestic Loafs:5  Nap Rights:1  <== Meowjority

[*] 36 block, so block hoa phieu: 0
[*] Ghe theo plurality : Meowjority 12, Nap Rights 9, Domestic Loafs 9, Tuna Reform 6
[*] Phieu toan hat     : Domestic Loafs 293 (27.5%), Meowjority 286 (26.8%), Tuna Reform 254 (23.8%), Nap Rights 234 (21.9%)
```

**Bước 3 - Kiểm chứng.** Hai đối chiếu độc lập với phép gán, chạy trong `exploit.py` và thoát lỗi nếu lệch:

```text
[*] doi chieu : 1067 cap, delay bo phieu min=560s max=1184s, so cap vote truoc check-in = 0
[*] kiem chung: 36/36 block co so phieu = so cu tri dang ky (tong 1067 = 1067 phieu)
```

Mỗi block nhận đúng số phiếu bằng số cử tri đăng ký của nó, xác nhận phép ghép phủ đủ dữ liệu. Phép đếm này không kiểm chứng độc lập việc từng phiếu được gán đúng cử tri. Bảng phân bố ghế cũng khớp với tình tiết của đề: Meowjority
dẫn 286/1067 phiếu (26.8%) nhưng giữ 12/36 block (33.3%), nhiều ghế nhất dù về nhì về số phiếu;
Domestic Loafs nhiều phiếu nhất (293) chỉ giữ 9 block. Biên cách biệt ở các block Meowjority thắng
là 1 đến 15 phiếu, trong đó Windowsill Way 6-5 và Scratching Post Street 11-9 là hai block sát nhất,
cả hai đều thắng sát nên đều phụ thuộc phép gán ở Bước 1.

Cờ là số block, không phải chuỗi có sẵn trong file, nên giá trị `cdctf{12}` chưa được đối chiếu qua
nộp bài; bằng chứng ở đây là toàn bộ dữ liệu 1067 phiếu khớp với 1067 lượt điểm danh và 36 block.

## Flag

```bash
python exploit.py files/catcounty_results.zip
```

```text
[+] Block Meowjority kiem soat:
      - Cardboard Court
      - Catnip Corner
      - Hairball Heights
      - Mousetrap Alley
      - Pawprint Plaza
      - Purrington Place
      - Scratching Post Street
      - Sunbeam Square
      - Tuna Terrace
      - Whisker Row
      - Windowsill Way
      - Yarnball Yard
[+] flag: cdctf{12}
```

## Reproduce

```bash
python exploit.py files/catcounty_results.zip     # loi giai day du, ghi flag.txt
python analysis/alignment.py files/catcounty_results.zip    # bang kiem chung phep gan theo lag
python analysis/sensitivity.py files/catcounty_results.zip  # so ghe Meowjority khi dich pha +/-1
```

## Danh sách 12 block để dùng cho Gerry the Larry (2/2)

Cardboard Court, Catnip Corner, Hairball Heights, Mousetrap Alley, Pawprint Plaza, Purrington Place,
Scratching Post Street, Sunbeam Square, Tuna Terrace, Whisker Row, Windowsill Way, Yarnball Yard.

36 tên block trong `info.csv` là cùng một danh sách precinct mà client của bài 2/2 hiển thị: client
dùng bảng 6x6 (36 ô) và ba tên trích từ bảng đó (Treat Jar Terrace, Cushion Hill, Biscuit Bend) đều
có mặt trong 36 block ở trên, nên hai bài dùng chung một bản đồ đơn vị bầu cử.
