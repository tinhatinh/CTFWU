import {JsonRpcProvider, Contract, computeAddress} from "ethers";

const RPC = "https://web-1a41803b1badce11.web.h7tex.com";
const SETUP = "0x152F449c1aCBf34E2337e33f10Cc3e0B8DCfb14c";
const KEY = process.env.CTF_PK || "0x<private key that GET / of the instance prints>";
if (!KEY.startsWith("0x") || KEY.length !== 66) {
  console.error("set CTF_PK to the 64-hex private key printed by GET " + RPC);
  process.exit(1);
}

const p = new JsonRpcProvider(RPC);
const w = new (await import("ethers")).Wallet(KEY, p);
const e = (x) => Number(x) / 1e18;

const setup = new Contract(SETUP, [
  "function pool() view returns (address)",
  "function lend() view returns (address)",
  "function token() view returns (address)",
  "function isSolved() view returns (bool)",
], p);

const pool = new Contract(await setup.pool(), [
  "function totalSupply() view returns (uint256)",
  "function balanceOf(address) view returns (uint256)",
  "function get_virtual_price() view returns (uint256)",
  "function token() view returns (address)",
], p);
const lend = new Contract(await setup.lend(), [
  "function totalDebt() view returns (uint256)",
  "function totalCollateralLP() view returns (uint256)",
  "function collateralLP(address) view returns (uint256)",
], p);
const token = new Contract(await setup.token(), [
  "function balanceOf(address) view returns (uint256)",
  "function owner() view returns (address)",
], p);

const player = computeAddress(KEY);
console.log("player", player);
console.log("blockNumber", await p.getBlockNumber());
console.log("player eth", e(await p.getBalance(player)));
console.log("pool", await pool.getAddress(), "lend", await lend.getAddress(), "token", await token.getAddress());
console.log("pool eth", e(await p.getBalance(await pool.getAddress())));
console.log("pool tok", e(await token.balanceOf(await pool.getAddress())));
console.log("lend tok", e(await token.balanceOf(await lend.getAddress())));
console.log("player tok", e(await token.balanceOf(player)));
console.log("totalSupply", e(await pool.totalSupply()));
console.log("player LP", e(await pool.balanceOf(player)));
console.log("vprice", e(await pool.get_virtual_price()));
console.log("totalDebt", e(await lend.totalDebt()), "totalCollLP", e(await lend.totalCollateralLP()));
console.log("owner", await token.owner());
console.log("isSolved", await setup.isSolved());
