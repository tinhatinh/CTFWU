# My Eyes Burn — Misc (Medium)

**Flag:** `sun{praisethesun}`
**Files:** `boardwriter.klc` (3562 B, UTF-16LE, CRLF)

## Đề bài

"anon hasn't been outside in years, so he put the sun in his keyboard. find the flag he types to bring it out."

Đề cho đúng một file `.klc` - nguồn layout bàn phím Windows do MSKLC sinh ra. Không có ciphertext nào cả, nên "the flag he types" phải là thứ tự phím tự thân layout định nghĩa.

## Phân tích

`.klc` là text UTF-16LE, đọc trực tiếp được, không cần tool. Hai quy tắc của định dạng là toàn bộ lời giải:

1. Trong bảng `KEYS`, ký tự có hậu tố `@` là dead key. File này chỉ có một: `29 OEM_3 0 0060@ 007e -1`, tức phím `` ` ``.
2. Trong khối `DEADKEY <state>`, dòng `<src> <res>@` có nghĩa: đang ở trạng thái chết `<state>`, gõ `<src>` thì chuyển sang trạng thái chết `<res>`; nếu `<res>` không có `@` thì nó được in ra thật và chuỗi dừng.

Phần còn lại của layout là QWERTY Mỹ chuẩn, không có gì đáng nghi.

Đếm được: 17 khối `DEADKEY`, một điểm vào (`0060`, vì nó không là kết quả của khối nào), và duy nhất một đầu ra không phải dead key:

```
DEADKEY 02b0
007d    2600          <- không có @  =>  U+2600 BLACK SUN WITH RAYS  =  ☀
```

Đúng nghĩa đen của "he put the sun in his keyboard": layout này chỉ ra được mặt trời ☀ bằng một chuỗi dead key, và "my eyes burn" là phản ứng khi nhìn thấy nó.

## Chuỗi khai thác

Đi đồ thị ngược từ `02b0` về điểm vào (mỗi trạng thái có đúng một dòng nên đường đi duy nhất, không cần tìm kiếm):

```
0060 + s -> 02D0    02EF + p -> 02BA    02BD + e -> 02CD    02EE + s -> 02D4
02D0 + u -> 02ED    02BA + r -> 02C9    02CD + t -> 02E4    02D4 + u -> 02E1
02ED + n -> 02B4    02C9 + a -> 02D3    02E4 + h -> 02D8    02E1 + n -> 02B0
02B4 + { -> 02EF    02D3 + i -> 02E9    02D8 + e -> 02EE    02B0 + } -> U+2600 ☀
02E9 + s -> 02BD
```

Gõ theo thứ tự: `` ` `` `s` `u` `n` `{` `p` `r` `a` `i` `s` `e` `t` `h` `e` `s` `u` `n` `}`

Backtick chỉ là dead key mồi (không in ra ký tự nào), nên văn bản hiện trên màn hình là:

```
sun{praisethesun}
```

## Flag
```
$ python solve_klc.py files/boardwriter.klc
[*] keystrokes: '`sun{praisethesun}'
[*] emits: ☀  (U+2600 BLACK SUN WITH RAYS)
[+] FLAG: sun{praisethesun}
```
