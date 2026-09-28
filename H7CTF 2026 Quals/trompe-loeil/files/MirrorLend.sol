// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./IERC20.sol";

interface IPool {
    function get_virtual_price() external view returns (uint256);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract MirrorLend {
    IPool public immutable pool;
    IERC20 public immutable token;
    mapping(address => uint256) public collateralLP;
    mapping(address => uint256) public debt;
    uint256 public totalDebt;
    uint256 public totalCollateralLP;

    constructor(address _pool, address _token) {
        pool = IPool(_pool);
        token = IERC20(_token);
    }

    function deposit(uint256 lp) external {
        require(pool.transferFrom(msg.sender, address(this), lp), "tf");
        collateralLP[msg.sender] += lp;
        totalCollateralLP += lp;
    }

    function borrow(uint256 amount) external {
        uint256 maxDebt = collateralLP[msg.sender] * pool.get_virtual_price() / 1e18;
        require(debt[msg.sender] + amount <= maxDebt, "undercollateralized");
        debt[msg.sender] += amount;
        totalDebt += amount;
        require(token.transfer(msg.sender, amount), "t");
    }
}
