// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./Token.sol";
import "./GenesisVault.sol";

contract Setup {
    Token public token;
    GenesisVault public vault;
    address public constant victim = address(0xC0FFEE);
    uint256 public constant PLAYER_FUNDS = 200 ether;
    uint256 public constant VICTIM_DEPOSIT = 100 ether;
    bool public victimDeposited;

    constructor(address player) {
        token = new Token();
        vault = new GenesisVault(address(token));
        token.mint(player, PLAYER_FUNDS);
        token.mint(address(this), VICTIM_DEPOSIT);
    }

    function victimDeposit() external {
        require(!victimDeposited, "done");
        victimDeposited = true;
        token.approve(address(vault), VICTIM_DEPOSIT);
        vault.deposit(VICTIM_DEPOSIT, victim);
    }

    function isSolved() external view returns (bool) {
        return victimDeposited
            && vault.balanceOf(victim) == 0
            && token.balanceOf(address(vault)) < 1 ether;
    }
}
