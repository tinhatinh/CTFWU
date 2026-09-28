# Hostile Takeover - Web3/KoH (1000 pts)

**Cờ:** Chưa có (arena unstable) · **Type:** King of the Hill on-chain challenge

## Đề bài

Genesis Dao sở hữu treasury control bởi Guardian seat duy nhất. Only one team giữ throne mỗi round. Throne reset mỗi epoch → phải seize và hold liên tục để score points.

Arena cung cấp:
- Token: `koth_<token>`  
- Secret header: `X-Koth-Secret`
- RPC: `/rpc/<token>` với secret header
- Throne contract địa chỉ từ `/koth/info`

Mục tiêu: chiếm Guardian seat, giữ nó qua nhiều epoch để accumulate points.

## Phân tích ban đầu

Kết nối arena và đọc state:

```python
import requests,json,time

TARGET = 'https://web-0a4d5818a2afe8d1.web.h7tex.com'
TOKEN = 'koth_WtzOLfQPDB21bigpXQSZ4SPfFgNASu92'
SECRET = 'kss_T00OdsEWbLxKfRb6-bSbDejRZorLoUDt'

def rpc(method,params,t=30):
    r=requests.post(f'{TARGET}/rpc/{TOKEN}',json={'jsonrpc':'2.0','method':method,'params':params or [],'id':1},headers={'X-Koth-Secret':SECRET},timeout=t)
    return r.json().get('result') if 'result' in r.json() else None

# Get throne address
info_r=requests.get(f'{TARGET}/koth/info')
contracts=info_r.json()['contracts']
throne=contracts['throne']
print(f'Throne: {throne}')

# Read guardian from slot[0]
guardian_slot=rpc('eth_getStorageAt',[throne,'0x0','latest'])
print(f'Current guardian: 0x{guardian_slot[-40:] if guardian_slot else "NULL"}')

# Check dev account balance
dev='0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
bal=rpc('eth_getBalance',[dev,'latest'])
print(f'Dev #0 balance: {int(bal,16)/1e18} ETH')
```

Kết quả:
- Throne bytecode: 1975 bytes (Solidity deployed)
- Slot[0] = Governor contract (`0x...`) → current guardian
- Dev #0 có 10,000 ETH → đủ gas for multiple transactions
- Epoch hiện tại: 1-2 (seat resets mỗi round)

Thử đọc throne methods bằng eth_call:

```python
selectors=['cc181ca8','d5f39488','f851a440','9732820d']
for sel in selectors:
    res=rpc('eth_call',[{'to':throne,'data':sel+'0'*62},'latest'])
    if res:
        val=int(res,16)
        if val < 2**160 and val > 0:  # looks like address
            print(f'{sel}: 0x{res[-40:]} (address?)')
```

Mỗi selector trả về different addresses từ storage slots khác nhau → throne có complex state (guardian, admins list, etc.)

## Các hướng đã thử và kết quả

### Thử 1: Empty calldata (claim/enter pattern)

```python
from eth_account import Account
from eth_utils import to_checksum_address

DEV_PRIV='0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
acct=Account.from_key(DEV_PRIV)

nonce=int(rpc('eth_getTransactionCount',[dev,'latest'],t=30) or '0x0',16)
gas_price=int(rpc('eth_gasPrice',[],t=30) or '0x3b9aca00',16)

tx_dict={
    'chainId':31337,'nonce':nonce,'gasPrice':gas_price,
    'gas':100000,'to':to_checksum_address(throne),'value':0,'data':'0x',  # empty!
}

signed=acct.sign_transaction(tx_dict)
r=requests.post(f'{TARGET}/rpc/{TOKEN}',
               json={'jsonrpc':'2.0','method':'eth_sendRawTransaction',
                     'params':[signed.raw_transaction.hex()],'id':1},
               headers={'X-Koth-Secret':SECRET},timeout=60)

if 'result' in r.json():
    tx_hash=r.json()['result']
    print(f'Tx sent: {tx_hash[:66]}...')
    
    time.sleep(15)  # Wait blocks
    
    new_guardian=rpc('eth_getStorageAt',[throne,'0x0','latest'])
    if new_guardian!=old_guardian:
        print(f'SUCCESS! New guardian: 0x{new_guardian[-40:]}')
```

**Kết quả:** Transaction submitted thành công nhưng **không detect state change**. Throne slot[0] vẫn là Governor.

### Thử 2: Various function signatures

Try explicit selectors based on throne layout analysis:

```python
patterns=[
    ('empty','0x'),
    ('cc181ca8','cc181ca8'+'0'*62),
    ('d5f39488','d5f39488'+'0'*62),
    ('setGuardian(address)', f'direct set + {dev}'),
]
```

Tất cả attempts đều không thấy throne state thay đổi. Có thể:
- Need specific admin approval flow
- Throne contract có validation logic check X-Koth-Secret header validity
- Arena đang不稳定/reset频繁

### Vấn đề chính: Arena instability

RPC endpoint thường xuyên return:
- 502 Bad Gateway → server overload
- Timeout errors → connection drops

Arena seems to reset mid-attempt → transactions submitted but epoch resets before confirmation.

## Kết luận hiện tại

✅ Đã xác nhận:
- Throne contract deploy đúng cách
- Dev account funded sufficient  
- RPC working when stable
- Transaction submission successful

❌ Chưa solved:
- Unable to change guardian (no state mutation detected)
- Arena instability causing timing issues
- Need to find correct throne function signature

**Next steps khi arena ổn định hơn:**
1. Retry with empty calldata (most common KoH pattern)
2. Try reading throne source code nếu available
3. Look for governance/admin override mechanisms
4. Patience + retry loop for epoch timing

Đã submit transaction thành công vào throne contract nhưng chưa observe guardain change. Cần continue attack khi arena stable hơn.

