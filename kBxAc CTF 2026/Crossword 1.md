---
title: "Crossword 1"
category: "Crypto"
tags: ["substitution-cipher", "crossword", "image-analysis", "monoalphabetic-substitution"]
solve_date: "2026-10-10T10:40:00+07:00"
language: "vi"
points: 100
---

# Crossword 1

**Tác giả:** ayushch  
**Đề:** *Fill this FOOT…* — dòng mô tả bị cắt trong dữ liệu được cung cấp; định dạng cờ là `kBxAc{...}`, còn chủ đề bóng đá được xác nhận từ chính lưới đã giải. Quy tắc dựng cờ nằm đầy đủ trong `instructions (1).txt`.  
**Flag:** in không rút gọn ở cuối writeup, 616 ký tự. Chưa lưu phản hồi submission.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `crossword1.zip` | 23,991 | `869fc3a85fc6c8c8a4b0e8e54f125f983df107b93fceabf78300c4c0f8a68e86` |
| `crossword.png` (bên trong ZIP) | 30,097 | `02eef3e60df6b12a7429055c592db0fb52f763c7268d74f628a113361c942ae8` |
| `instructions (1).txt` | 1,006 | `1cc1b70a9a507046a4182924039d140ce800c2ec49fc93b01f7b1b41f919ae34` |

`instructions (1).txt` có cùng SHA-256 với file hướng dẫn của **Crossword 2**: hai bài dùng chung một bộ quy tắc, chỉ khác độ khó của lưới.

## Đề bài và quy tắc dựng flag

Mỗi chữ cái trong lưới đã bị thay bằng **một số được gán ngẫu nhiên trong 1–26**, không phải bảng `1=A, 2=B, ...`. Phải khôi phục song ánh số → chữ bằng cách giải các từ giao nhau.

Sau khi giải xong: đọc chữ cái **trái sang phải theo từng hàng**, bỏ ô trống, giữ thứ tự hàng **trên xuống dưới**, nối các hàng bằng `_`, rồi bọc trong `kBxAc{...}`. Đề kèm ví dụ minh họa cách một hàng chứa nhiều từ vẫn được nối liền thành một chuỗi.

## Phân tích ảnh

`crossword.png` là ảnh nhị phân thuần `1480×1520`, không có chunk phụ, không có dữ liệu sau `IEND`, không có pixel trung gian (chỉ hai giá trị 0 và 255). Lưới có **37 cột × 38 hàng**, pitch 40 px, mỗi ô là khối trắng `36×36` chứa một hoặc hai chữ số màu đen. Tổng cộng **572 ô có dữ liệu**.

Cắt mỗi ô theo cửa sổ `38×38` trên lưới 40 px rồi gom raw bytes bằng `Counter` cho ra **đúng 27 mẫu**: một mẫu trắng xuất hiện 834 lần và 26 mẫu số. Mỗi mẫu ứng với một giá trị số duy nhất, nên toàn bộ bài quy về việc định danh 26 mẫu — không cần đọc số cho từng ô.

## Định danh 26 giá trị

Tách connected component các nét đen trong từng ô cho biết ô có một hay hai chữ số: **183 ô một chữ số** và **389 ô hai chữ số**. Gom toàn bộ nét chữ thu được 20 dạng glyph, tức 10 chữ số × 2 kiểu render: glyph cao 28 px dùng cho ô một chữ số, glyph cao 21 px dùng cho ô hai chữ số.

Độ đậm ở đây **không phải tín hiệu ẩn**. 183 ô một chữ số khớp chính xác tổng số ô mang giá trị 1–9, và không ô một chữ số nào nhận giá trị ≥ 10. Font chỉ vẽ số có một chữ số lớn hơn cho đầy ô.

Ràng buộc quyết định là mọi giá trị phải nằm trong 1–26. Chữ số hàng chục chỉ có thể là `1` (207 ô) hoặc `2` (182 ô); với hàng chục `2`, hàng đơn vị bị chặn ở 0–6. Đếm vị trí từng glyph hàng đơn vị:

```text
digit  after-tens-1  after-tens-2   total
  0             3             16       19
  1             8              2       10
  2            16             38       54
  3            28              2       30
  4            13             45       58
  5             9             30       39
  6            37             49       86
  7            20              0       20
  8            40              0       40
  9            33              0       33
```

Đúng ba glyph không bao giờ đứng sau hàng chục `2` — chúng là `{7,8,9}`, vì `27`, `28`, `29` đều không hợp lệ. Ba glyph này phân biệt được bằng hình dạng: `7` là gạch ngang đầu cộng nét chéo xuống trái, `8` là hai vòng khép có eo ở giữa, `9` là vòng kín cộng nét descender bên phải. Bảy glyph còn lại là `{0,1,2,3,4,5,6}`, trong đó `0` nhận ra nhờ nét chéo bên trong vòng (số không gạch chéo).

Ghép bảng glyph–số vào lưới cho ra các chuỗi chữ chưa biết khóa. Các chuỗi dài nhất là neo, nhờ mẫu chữ lặp và các giao điểm: chuỗi 12 ô khớp `CHAMPIONSHIP` (mẫu `ABCDEFGHIBFE`), chuỗi 13 ô khớp `COUNTERATTACK`, chuỗi 10 ô mẫu `ABCCDCCEBF` khớp `POSSESSION`, và `MIDFIELDER`, `SUBSTITUTE`, `REFEREE` cũng phù hợp với các giao điểm. Chuỗi 15 ô duy nhất không khớp từ điển nào vì thực chất là hai từ liền nhau trong cùng một cột: `PENALTY` + `SHOOTOUT`.

## Khóa thay thế

```text
1=W  2=D  3=E  4=K  5=Z  6=J  7=S  8=M  9=U  10=V  11=G  12=P  13=L
14=B 15=Y 16=C 17=H 18=R 19=O 20=F 21=Q 22=I 23=X 24=T 25=N 26=A
```

Bốn chữ cái hiếm nhất (`Z`, `J`, `X`, `W`) chỉ chiếm 12 ô và được chốt nhờ các từ `EQUALIZER`, `INJURY`, `JERSEY`, `EXTRATIME`, `FIXTURE`, `WHISTLE`, `SWEEPER`, `WINGER`, `FORWARD`, `DRAW`, `YELLOWCARD`.

## Mã giải (Python 3 + Pillow)

Chạy cùng thư mục có `crossword1.zip`. Do các mẫu tile có nhiều cặp cùng tần suất (38, 16, 3, 2), danh sách `labels` được xếp theo **thứ tự từ điển trên raw bytes của tile** để tất định, không theo tần suất.

```python
from PIL import Image
from collections import Counter
from io import BytesIO
import zipfile

# number -> letter, recovered from the intersecting crossword words
number_to_char = {1:'W',2:'D',3:'E',4:'K',5:'Z',6:'J',7:'S',8:'M',9:'U',10:'V',11:'G',
                  12:'P',13:'L',14:'B',15:'Y',16:'C',17:'H',18:'R',19:'O',20:'F',21:'Q',
                  22:'I',23:'X',24:'T',25:'N',26:'A'}

# the 26 tile classes, in lexicographic order of their raw tile bytes
labels = [5,7,9,8,3,2,6,1,4,25,20,23,22,26,21,24,15,17,10,19,18,13,12,16,11,14]

with zipfile.ZipFile('crossword1.zip') as z:
    im = Image.open(BytesIO(z.read('crossword.png'))).convert('L')
    W, H = im.size
    tiles = [[im.crop((c*40, r*40, c*40+38, r*40+38)).tobytes() for c in range(W//40)]
             for r in range(H//40)]
    counts = Counter(t for row in tiles for t in row)
    blank = counts.most_common(1)[0][0]
    uniq = sorted(t for t in counts if t != blank)
    assert len(uniq) == 26, len(uniq)
    tile_to_char = {t: number_to_char[n] for t, n in zip(uniq, labels)}
    rows = [''.join(tile_to_char[t] for t in row if t != blank) for row in tiles]
    flag = 'kBxAc{' + '_'.join(r for r in rows if r) + '}'
    print(flag)
    print('rows', sum(1 for r in rows if r), 'letters', sum(len(r) for r in rows), 'len', len(flag))
```

Output:

```text
rows 38 letters 572 len 616
```

## Kiểm chứng

Kết quả có **38 đoạn hàng**, **37 dấu gạch dưới** và **572 chữ cái** — trùng đúng số ô có dữ liệu của lưới, nên không ô nào bị nhân đôi hoặc bỏ sót.

Toàn bộ 96 chuỗi tối đại (50 ngang, 46 dọc) độ dài ≥ 4 đều là thuật ngữ bóng đá hợp lệ: `CHAMPIONSHIP`, `COUNTERATTACK`, `MIDFIELDER`, `GOALKEEPER`, `QUARTERFINAL`, `TOURNAMENT`, `SUBSTITUTION`, `YELLOWCARD`, `WORLDCUP`, `CENTREBACK`, `ADVANTAGE`, `TARGETMAN`, `PLAYMAKER`, `EQUALIZER`… Không còn ô nào nằm ngoài một từ hợp lệ, các giao điểm và số ô đều nhất quán với bảng thay thế đã dựng.

SHA-256 của **chuỗi flag UTF-8, không có newline**:

```text
01b9b0086a3089c0ab567ca77b20ad9807fdc34345025ec4e338447de8a6d30c
```

## Flag đầy đủ (không rút gọn)

```text
kBxAc{WHISTLESCOMEBACK_OFULLBACKMEP_UUIVCHAMPIONSSCREST_SCOUTNENCTET_HSEHMATCHHCROSSA_LASWEEPERGKTISD_KILMALCENTREBACKII_INHANDBALLRERENU_CLEATSNEYOCPGRGM_KHRMSOEE_OBOOTSPASSINJURYTIME_FTHKTM_HALFTIMEGIERA_CCOUNTERCHAMPIONSHIP_OFFSIDEFAPQCOH_RORLEAGUECAPTAINJERSEY_NRWINGERKDAQNCEE_EMOEELUCOUNTERATTACK_RAREKSEMIFINALSOS_TLXIPZRVSFO_IDTACKLEETPOSSESSION_SOCCERKREFEREEPLUBX_NUATRELBATTACK_TPTCOACHDEFENSESRU_RHIUIAYTRD_ACADEMYBRACEFINALMIDFIELDER_NTENYATTF_STGOALPENALTYUE_FROMLDSUBSTITUTION_EIAEFLVHEDRIBBLE_RCLNOOAYOUTHE_KPTHROWINOACREDCARD_ANCHORWCTTBALLE_SSAAAFOULEDRAWK_SPITCHRRGUEABII_IDDETINJURYNET_S_TACTICS}
```

## Kết luận

Điểm then chốt là ràng buộc "mọi giá trị nằm trong 1–26" tự nó chỉ ra ba chữ số lớn `{7,8,9}` mà không cần đoán trước, biến bài toán từ một cryptogram mở thành một bảng phân loại hữu hạn. Khóa thay thế **không phải** đáp án: đề yêu cầu đọc **mọi chữ cái** trong lưới theo từng hàng, kể cả sáu ô chỉ thuộc các từ ba ký tự `KIT` (cột 31, hàng 33–35) và `NET` (hàng 35, cột 29–31) ở góc dưới phải — những chuỗi ngắn hơn mọi độ dài từ khác và dễ bị bỏ qua nếu chỉ trích các từ dài.
