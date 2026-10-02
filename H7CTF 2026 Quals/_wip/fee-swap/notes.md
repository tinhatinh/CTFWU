# Fee Swap - decision log

**Trạng thái: CHƯA có cờ.** `web3.h7tex.com:42600` ngừng trả banner (connect OK,
0 byte, đóng ngay) kể từ sau ~25 phiên dò protocol. Đã dừng sau 3 lần failure
giống nhau trên cùng primitive, không spam.

## A. ĐÃ XÁC NHẬN BẰNG TOOL OUTPUT (trên đích sống)

### Hoãn xuất hiện (cập nhật lúc 12:2x)
Kết nối được nhưng 0 byte, đóng ngay. 5 lần liên tiếp, tính cả lần chờ 4 phút.
=> đã dừng theo quy tắc "3 lần failure giống nhau trên cùng primitive".
Khi dịch hồi phục, chạy đúng thứ tự: `python exploit.py health`, rồi `probe`, rồi `main`.
Bài Countersign trong cùng session cũng dính đúng mẫu này nên đây là hạn mức của
nền tảng, không phải tín hiệu bài sai.

### Banner (mỗi phiên sinh bộ key khác nhau - đã thấy 3 bộ khác nhau)
```
program / user / authority / pool / mint_a / mint_b / vault_a / vault_b /
user_a / user_b / token_program / reserve_b
reserve_b = 100000000        (100 token, DECIMALS=6)
token_program = TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb   (SPL Token-2022)
num accounts:                 <- prompt, chờ input
```

### Máy trạng thái của protocol
| Đã gửi | Dịch trả về |
|---|---|
| `0` | `ix len: ` |
| `0` → `9` → `010a00000000000000` | `swap reverted` → `num accounts: ` → `ix len: ` (lặp lại) |
| `1` → `<pubkey>` | `vault_b remaining: 100000000` + `reserve not drained. no flag.` rồi **EOF** |
| `2` → `<pk>` (chỉ 1 dòng) | như trên |
| `10` → 10 dòng pubkey | như trên |
| `10` → 1 dòng "pk1 pk2 ... pk10" | như trên |

=> bản chất: **một phiên chỉ chạy ĐÚNG MỘT lần**, kết thúc bằng dòng verdict rồi
đóng socket. `swap reverted` là nhánh **chương trình lỗi**; `vault_b remaining:`
là nhánh **kết thúc phiên**. Hai chuỗi này phân biệt được nên làm oracle tốt.

### Grammar của một dòng account (đo bằng cách xem khi nào tới được `ix len:`)
```
"<address> <owner>"                      -> OK (đạt tới 'ix len:')
"<address> <owner> <lamports>"           -> OK
"<address> <owner> <lamports> <data-hex>"-> OK
"<address>"                              -> die (thiếu field)
"<address> 0"  / "<address> 1"           -> die (field 2 BẮT BUỘC là pubkey)
"role-name" (pool / user_a / ...)        -> die
"pk,true,true" / "pk:1:1" / "pk RW" / JSON -> die
```
**Đây là phát hiện quan trọng nhất:** harness cho phép *khai báo account mới*
theo dạng `address owner [lamports] [data]`, tức là **tự supplying state on-chain**.
Không có chi tiết này thì bài gần như không giải được bằng đúng 11 account có sẵn.

## B. PHÂN TÍCH lib.rs (đọc source, chưa đối chiếu hành vi trên đích)

`swap()` chỉ kiểm tra: `pool.owner == program`, `initialized`, `user.is_signer`,
`authority == PDA("authority")`, và `vault_src/vault_dst == p.vault_a/p.vault_b`.

**KHÔNG kiểm tra:** `user_src`, `user_dst`, `mint_src`, `mint_dst`, và
`token_program` (program id dẫn thẳng vào `invoke`, tức là chọn được luôn).

Hai hệ quả:
1. `mint_src` không bị đối chiếu với `p.mint_a`, và `user_src` không bị bắt buộc
   là tài khoản do user sở hữu theo nghĩa "thật" - spl-token chỉ kiểm tra
   `user_src.mint == mint_src == vault_src.mint`, `decimals == 6`, và
   `AccountOwner == user` (là signer). **Một token account tự dựng
   (mint_a, owner=user, amount khổng lồ) thỏa mãn tất cả.**
2. `payout = amount - amount*100/10000` luôn `<= amount`, nên không có overflow
   hay underflow nào ăn được; không thể lấy nhiều hơn `amount` trong một lần.

### Kế hoạch drain
Dựng `user_src` giả với `amount = 10**15` của `mint_a`, gọi `SwapAToB` với
`amount = vault_b` hiện tại. Nộp A (từ túi giả, vào `vault_a` thật) → nhận về
`payout = amount - amount//100` B từ `vault_b` thật vào `user_b` thật.
Vòng lặp: `1e8 → 1e6 → 1e4 → 100 → 1 → 0`, vì khi `amount < 100` thì
`amount//100 == 0` nên **fee = 0**, rút được chính xác phần còn lại → reserve = 0.

## B2. HAI CHỖ ĐỌC SAI CỦA CHÍNH TÔI (sửa bằng cách đọc lại log, không cần tool mới)

1. **"Không swap nào chạy được" là kết luận sai.** Mẫu chứng minh `ix len:` là
   `<addr> <owner>` (2 field). Nhưng mọi dòng mà tôi ghi nhận là "có account list
   → ra ngay verdict, không thấy `swap reverted`" lại đến từ các thử nghiệm
   **1 field** (`<pubkey>` trần) - tức là submit sai cú pháp, bị từ chối trước khi
   chạy. Nói cách khác tôi đã lấy kết quả của input hỏng để phủ nhận primitive.
   Đường đi đúng (`10` + 10 dòng 2-field → `ix len` → data) **chưa bao giờ được
   gửi lên dịch** vì ngay sau đó tôi vướng bug parse banner rồi dịch chết.
2. **"Phải rút dần nhiều vòng" là sai và sẽ thất bại.** Mỗi kết nối chỉ chạy ĐÚNG
   MỘT attempt rồi đóng socket, và `reserve_b` luôn là 100000000 ở banner mới
   (validator khởi tạo lại theo phiên), nên không có "vòng 2". Bài rút phải gọn
   trong MỘT swap. Điều đó khả dụng và đã chứng minh đóng được:
   `payout(a) = a - floor(a/100)`; viết `a = 100q + r` (0<=r<100) thì
   `payout = 99q + r`, nên với reserve `R = 99q + r` chọn
   **`a = 100*(R//99) + (R % 99)`** ta có `payout == R` CHÍNH XÁC, và `a <= 1.0102*R`.
   Ví dụ `R = 1e8 -> a = 101010101 -> payout = 100000000` -> reserve về 0.
   Đã kiểm 5000 giá trị liên tiếp + 30000 giá trị ngẫu nhiên tới 2^63: 0 lỗi.
   (Lần kiểm đầu tôi tìm `a` trong cửa sổ `R..R+300` nên báo "không có nghiệm" -
   cửa sổ sai, không phải hàm sai.)

## B3. BA KE HOACH, THU TU CHI PHI (da mo phong bang `analysis/simulate.py`)

Simulator mo phong `swap()` + cac rule cua spl-token (mint binding, decimals @44,
so du, **nguoi ky phai la owner cua tai khoan nguon**). Ca 5 control deu dat voi
LI DUNG DANG (C2 thieu du, C3 sai mint, C4 vault khop pool, C5 source khong cua user).
Ket qua tren duoc luu o `analysis/simulate.txt`.

| # | Ke hoach | Dependency | Ket qua model |
|---|---|---|---|
| 1 | `honest` - swap 1:1 bang A that, `amount = exact_amount(reserve)` | chi can `user_a` du A | `1e8 -> 0` DRAINED |
| 2 | `rich` - khai bao token account gia (mint_a, owner=user, 1e15) lam nguon | harness dung `data-hex`; MOT nuoc | `1e8 -> 0` DRAINED |
| 3 | `rogue` - pool gia + self-transfer `user_a -> user_a` | 2 nuoc + spl-token cho self-transfer | `1e8 -> 0`, `user_a` giu nguyen |

**Reframe quan trong:** `honest` chay duoc nghia la bai nay co the KHONG co loi
trien khai nao ca - de bai noi "a clean 1:1 desk with a healthy B reserve it's sure
it can always cover", va neu `user_a` duoc an trieu nhieu A hon reserve B (100 B
so voi >=101.01 A) thi "walk out with the entire B reserve" chi la... mua het hang.
Do la gia thiet toi da bo qua vi cho rang "phai co bug", trong khi no la nuoc re
nhat va tra loi luan duoc. Neu no thanh cong thi `rich`/`rogue` chi la bo nhoi.

## C. CÒN THIẾU (chưa chứng minh được)

1. **Chưa lần nào chạy được một swap hợp lệ.** Mọi phiên có account list đều kết
   thúc bằng verdict mà không thấy `swap reverted`, nghĩa là nhiều khả năng
   harness *bỏ qua* instruction khi nó không parse được danh sách của tôi - chứ
   chưa chắc chương trình đã chạy. Cần một lần `vault_b remaining:` **khác**
   `100000000` để chứng minh primitive hoạt động.
2. **Chưa biết harness có thực sự tạo account từ `data-hex` hay không** (hay chỉ
   đọc 2 field đầu). Đây là mắt xích quyết định của cả chain.
   Kế hoạch phân biệt: `probe` ( nguồn thật `user_a`, amount nhỏ) nếu ra
   `swap reverted` => instruction CÓ chạy, và revert là do dữ kiện; nếu im lặng
   ra verdict => harness bỏ qua instruction khi danh sách account có field lạ.
3. Chưa biết flag in ra ở đâu khi `reserve_b == 0` (dòng verdict mới, hay một
   artifact kèm theo).

## D. Việc cần làm khi dịch hồi phục

Theo thứ tự rẻ → đắt, mỗi bước chỉ một kết nối:
1. `0` / `9` / `010a00000000000000` → vẫn phải ra `swap reverted` (kiểm tra health).
2. Danh sách 10 account thật theo đúng thứ tự `lib.rs`
   (`pool authority user user_a user_b vault_a vault_b mint_a mint_b token_program`),
   mỗi dòng `<addr> <owner>`, data = `SwapAToB{amount:10}`.
   Kỳ vọng: hoặc `swap reverted`, hoặc `vault_b remaining: 99999991`.
   Đây là **bài kiểm tra quyết định** rằng instruction có thực sự chạy.
3. Nếu bước 2 revert: thử đổi `owner` của `pool` thành `program`, của các token
   account thành `token_program` (tôi đã đoán vậy), và thử bỏ/lamports khác 0.
4. Nếu bước 2 chạy: thêm account giả (`<newaddr> <token_program> <lamports>
   <165-byte token account layout>`) làm `user_src`, amount lớn → rút dần như mục B.

`exploit.py` đã viết sẵn đường đi này (`round_swap`), kèm self-test cho base58 +
layout 165 byte. `exploit.py` đã viết sẵn đường đi này (`round_swap`), kèm self-test cho base58 +
layout 165 byte.

## E. Bẫy đã tránh / đã mắc
- `So13zg1uQ3b8v6PdEHnQTv4qfQtLJUqX7peu1b5QfzP` tôi định dùng làm "native loader"
  là **trí nhớ sai** (đó là id của wrapped SOL mint). Đã thay bằng SYSTEM và cắt
  bỏ mọi hằng số tự bịa; chỉ giữ các id kiểm chứng được bằng decode.
- Sai lầm dây A: mất rất nhiều vòng để đoán grammar vì tôi đọc socket theo cửa sổ
  thời gian cố định, nên verdict của dòng N bị gán nhầm cho dòng N+1. Chỉ hết mù
  khi chuyển sang "đọc tới khi gặp prompt kết thúc bằng `: `" và dùng
  `swap reverted` làm control dương.

## File
`files/{lib.rs,Cargo.toml}` (đầu vào gốc), `exploit.py`,
`analysis/{svc,proto,proto2,talk,raw,accfmt,atk,b58}.py`, `analysis/livewin.txt` (trống).
