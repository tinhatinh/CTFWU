# notes.md - lottery

Input: `files/Lottery.sol` (1153 B, sha256 `38f58ac24b5c9e8ac0d31195ba1e4ae489bf51b6a00f47320231fb6891df88b5`), `files/Setup.sol` (314 B, sha256 `ebb2b795e85b9c713341ab32b4bb106e2ece698658c73417e3e79b5ab866ab06`)
Định dạng cờ đề yêu cầu: `CSSCTF{CSS{...}}` với `CSS{...}` lấy từ nc

## H1 - `Setup (2).sol` là Setup của bài Lottery
cmd: `for f in Setup*.sol; do cat "$f"; done`
evidence: `Setup (2).sol` 314 byte chứa `Lottery public lottery;` và `isSolved() = lottery.winner() != address(0)`; bản 842 byte (`Setup.sol` tải hôm 26/9) là của bài DEX khác (Token/Pool/MirrorLend). Lần đọc đầu tiên qua đường dẫn attachment lại trả đúng nội dung bản 842 byte.
result: OK - điều kiện thắng chỉ cần `winner != 0`, winner là contract cũng được. Luôn `cat` file có tên khoảng trắng/`(n)` thay vì tin nội dung trả về theo attachment.

## H2 - Đọc `random()` bằng `eth_call` ở `latest` rồi gửi `guess` riêng
cmd: `python lab.py` (8 vòng guess)
evidence: 0/8 đúng. Chuỗi dự đoán và kết quả lệch nhau đúng một nhịp: `target` của tx vừa rồi bằng `pred` của vòng kế tiếp, tức `eth_call` mô phỏng ở block `tip` trong khi tx rơi vào block `tip+1`, mà `blockhash(block.number-1)` thì đổi theo block.
result: DEAD - tx luôn nằm ở block khác block mà `eth_call` đã giả lập.

## H3 - Đọc `random()` ở block `pending`
cmd: `python lab2.py`, `python lab4.py` với anvil `--block-time 3`
evidence: 0/6 ở auto-mine; 0/12 ở `--block-time 3`; 10 tx xếp hàng bằng nonce liên tiếp không chui vào cùng một block (10 block được đào, `streaks` trả 0).
result: DEAD - anvil đào block theo tx, `pending` không phải block mà tx sẽ rơi vào.

## H4 - Tự tính keccak của block kế tiếp ngoài chain
cmd: `python lab3.py` (đo delta timestamp giữ hai block liên tiếp)
evidence: `ts delta after one tx: 0`, có lúc lại là 1; anvil lấy timestamp theo đồng hồ thật. `block.difficulty` = 0 và `blockhash(tip)` thì đã biết, nhưng không có hàm dự đoán delta.
result: DEAD - không chốt được `block.timestamp` của block tương lai.

## H5 - Đoán trong cùng transaction
cmd: `RPC=http://127.0.0.1:8547 python solve.py` (anvil local, `Setup.sol` + `Lottery.sol` của đề)
evidence: `run(10)` status 1, `streaks(attacker) = 10`, `winner = attacker`, `isSolved: True`. Cùng tx thì `random()` là hằng số nên 10/10.
result: OK - primitive chính, đã xác nhận lại trên instance thật.

## H6 - Launcher không tạo được instance
cmd: `printf '1\n<ticket>\n' | python drive.py` (16 lần, 13:50 - 15:34)
evidence: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` tại `eth_sandbox/launcher.py:99 data = requests.post(`. `GET :8546/` → `sandbox is running!` HTTP 200 0.42 s. `POST :8546/new` với bearer giả → `{"error":"nice try","ok":false}` HTTP 200 32 byte, nên route và nhánh xác thực còn sống. RPC proxy vẫn trả `invalid uuid specified`.
result: DEAD - lỗi ở `launch_node` phía ban tổ chức, không phải cách gọi của mình. Đã tự hồi phục lúc 15:51 mà không cần ai sửa. Probe `POST /new` bearer giả là kênh chẩn đoán miễn phí, không tốn hạn mức launch.

## H7 - Ticket chứa ký tự Cyrillic làm launcher crash
cmd: `printf '1\nR3:TURI\n'` và `printf '1\naaaaaaaa\n'`
evidence: ticket ASCII thuần cũng fail y hệt, và về sau chính ticket `R3:TURИ` launch thành công.
result: DEAD - không có liên quan.

## H8 - Diệt instance đang chạy để launch lại với ticket "đúng tên đội"
cmd: `printf '2\nwrongticket\n'` → `Instance killed`
evidence: ticket không bị kiểm tra lúc launch (mọi chuỗi đều được cấp instance), còn uuid/private key/setup chỉ tồn tại trên socket đã đóng. Hành động `3` đọc `/tmp/<team_id>` do launcher ghi, tức cờ bind theo ticket chứ không theo IP.
result: DEAD - tự xoá lease duy nhất đang có. Không bao giờ lặp lại: launch bằng ticket nào cũng được, cứ solve rồi lấy cờ.

## H9 - Instance sống nhưng response bị cắt
cmd: `curl -X POST .../eth_accounts`, `.../eth_sendTransaction`, `python exploit_live.py`
evidence: `eth_accounts` = `0xACCCF717...` (deployer) và `0x6fbc29b5...` (player), mỗi account `0x10f0cf064dd59200000` = 5000 ETH. `eth_sendTransaction` được proxy cho qua và node tự ký. `anvil_impersonateAccount` → `invalid request`. Setup = CREATE(deployer, 0) = `0xE5Bf39E2a633f350eA183716b898b601530cBc85` (726 byte), `lottery()` → `0x13b4Edba63FAcaDC68232DAFDAaF31f76Ca72A3b`.
result: OK - không cần dòng private key bị mất. Instance thật là mainnet fork: chainId `0x1`, tip `26096389`.

## H10 - Xác minh hợp đồng by so bytecode
cmd: `eth_getCode(setup) == compiled deployedBytecode`
evidence: `False` trên instance thật nhưng `True` trên replica local, do solc của tác giả khác 0.8.20 (metadata hash lệch). Kích thước thì khớp: 726 byte.
result: DEAD - thay bằng `eth_call lottery()`; chỉ dùng size làm đối chiếu.

## H11 - Chốt trên instance thật
cmd: `RPC=... PLAYER=0x6fbc29b5... python exploit_live.py` rồi `printf '3\nR3:TURИ\n'`
evidence: `run(10) status: 0x1 gasUsed: 135055`, `winner: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2`, `isSolved: True`; nc in `CSS{U5E_4_R4ND0M_FUNCT10N}` hai lần (15:55:15, 15:56:03) giống hệt nhau; `2` + ticket trả `Instance killed`.
result: OK - cờ: `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}`

---

Nguyên tắc ghi: không xoá nhánh sai, chỉ thêm `result: DEAD - <lý do>`, để lần sau đọc lại không thử trùng.
