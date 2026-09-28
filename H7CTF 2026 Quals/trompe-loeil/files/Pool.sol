// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./IERC20.sol";

contract Pool {
    IERC20 public immutable token;
    string public name = "Mirror LP";
    string public symbol = "mLP";
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    constructor(address _token) {
        token = IERC20(_token);
    }

    receive() external payable {}

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 a = allowance[from][msg.sender];
        if (a != type(uint256).max) allowance[from][msg.sender] = a - amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function get_virtual_price() public view returns (uint256) {
        if (totalSupply == 0) return 1e18;
        return (address(this).balance + token.balanceOf(address(this))) * 1e18 / totalSupply;
    }

    function addLiquidity(uint256 tokenAmount) external payable returns (uint256 lp) {
        uint256 valueBefore = address(this).balance - msg.value + token.balanceOf(address(this));
        require(token.transferFrom(msg.sender, address(this), tokenAmount), "tf");
        uint256 added = msg.value + tokenAmount;
        lp = totalSupply == 0 ? added : added * totalSupply / valueBefore;
        totalSupply += lp;
        balanceOf[msg.sender] += lp;
    }

    function removeLiquidity(uint256 lp) external {
        uint256 ethOut = address(this).balance * lp / totalSupply;
        uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
        balanceOf[msg.sender] -= lp;
        totalSupply -= lp;
        (bool ok, ) = msg.sender.call{value: ethOut}("");
        require(ok, "eth");
        require(token.transfer(msg.sender, tokenOut), "tok");
    }
}
