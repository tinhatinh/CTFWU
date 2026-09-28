# notes.md - Trompe-l'œil

Điều kiện thắng: `lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18`
Nghĩa là phải vay được nhiều hơn giá trị thế chấp **tính theo giá tại thời điểm chấm**, nên
chỉ có hai đường: hoặc làm giá giảm sau khi vay, hoặc làm giá tăng đúng lúc vay rồi để nó
tụt lại. Đề bài ("chỉ cần giữ được chừng nào mắt còn nhìn") chọn đường thứ hai.

## H1 - donate rồi rút lại để hạ giá
cmd: đọc `Pool.sol`
evidence: tài sản của pool chỉ ra khỏi pool qua `removeLiquidity`, và hàm này chia đúng tỷ lệ
`lp/totalSupply` cho cả ETH lẫn token nên giá không đổi. Quyên góp trực tiếp làm giá tăng
vĩnh viễn, không rút lại được.
result: DEAD - không có cách hạ giá sau khi vay.

## H2 - tự mint Token
cmd: `readelf`-style đọc `Token.sol`
evidence: `owner = msg.sender` của constructor, tức là chính Setup; `Setup` không có hàm
mint nào forward. Player không điều khiển owner.
result: DEAD.

## H3 - mint LP rẻ bằng lỗi `valueBefore`
cmd: tính tay `addLiquidity`
evidence: `valueBefore = balance - msg.value + token.balanceOf(pool)` lấy số token **trước**
`transferFrom`, nhưng `added = msg.value + tokenAmount` nên tỷ lệ vẫn đúng; quyên góp token
trước rồi addLiquidity cũng cho giá không đổi.
result: DEAD - math của addLiquidity tự nhất quán.

## H4 - giá ảo trong callback của `removeLiquidity` (ĐÚNG)
cmd: đọc `Pool.sol:53-61`
evidence:
```solidity
balanceOf[msg.sender] -= lp;  totalSupply -= lp;   // supply đã giảm
(bool ok,) = msg.sender.call{value: ethOut}("");   // <- callback chạy ở đây
require(token.transfer(msg.sender, tokenOut));     // phần token CHƯA bị trừ
```
Trong callback, tử số vẫn tính đủ phần token chưa trả còn mẫu số đã giảm -> giá ảo cao hơn
giá thật. Hiệu ứng mạnh khi pool lệch về phía token.
result: PENDING -> xác nhận ở H5.

## H5 - tính số liệu và chạy
cmd: `node exploit.mjs`
evidence:
- `addLiquidity(100e18)` với `msg.value = 0`: E=10, T=110, S=120, giá vẫn 1e18, ta có 100 LP.
- `deposit(50)` vào MirrorLend, còn 50 LP để đốt.
- `removeLiquidity(50)` -> `ethOut = 10*50/120 = 4.1667`; trong callback
  `price = (10-4.1667 + 110) / 70 = 1.6547619e18`.
- `borrow(50 * 1.6547619) = 82.73809523809524` (reserve 1000 đủ lớn).
- Callback trả về, token được chuyển đi, giá về đúng 1e18.
On-chain sau tx: `vprice 1  totalDebt 82.73809523809524  collateralValue 50  isSolved true`.
result: OK - `GET /flag` -> `H7CTF{0bba5486-eebc-4ee8-a3de-a55e80c787f1}`

## Ghi chú công cụ (Windows, không có foundry)
- `npm i ethers@6 solc@0.8.24` là đủ; không cần forge/cast.
- solc-js trả bytecode tại `out.contracts[file][name].evm.bytecode.object` (có tiền tố `evm.`).
- ethers v6 dùng `new Interface(abi).encodeDeploy([arg])`, không có `encodeDeployData`.
- Receipt của node JSON-RPC này **không có** trường `transactionHash`; log bằng `rc.status`
  và `rc.blockNumber`.
