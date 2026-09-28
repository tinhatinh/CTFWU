// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./Token.sol";
import "./Pool.sol";
import "./MirrorLend.sol";

contract Setup {
    Token public token;
    Pool public pool;
    MirrorLend public lend;

    constructor(address player) payable {
        require(msg.value == 10 ether, "seed");
        token = new Token();
        pool = new Pool(address(token));
        lend = new MirrorLend(address(pool), address(token));

        token.mint(address(this), 10 ether);
        token.approve(address(pool), 10 ether);
        pool.addLiquidity{value: 10 ether}(10 ether);

        token.mint(address(lend), 1000 ether);

        token.mint(player, 100 ether);
    }

    function isSolved() external view returns (bool) {
        return lend.totalDebt() > lend.totalCollateralLP() * pool.get_virtual_price() / 1e18;
    }
}
