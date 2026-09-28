// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IERC20 {
    function transfer(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

contract GenesisVault {
    IERC20 public immutable asset;
    string public name = "Genesis Vault Share";
    string public symbol = "gVLT";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    uint256 public reserve;
    mapping(address => uint256) public balanceOf;

    event Deposit(address indexed caller, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed caller, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);
    event Sync(uint256 reserve);

    constructor(address _asset) {
        asset = IERC20(_asset);
    }

    function totalAssets() public view returns (uint256) {
        return reserve;
    }

    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply;
        return supply == 0 ? assets : assets * supply / reserve;
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply;
        return supply == 0 ? shares : shares * reserve / supply;
    }

    function previewDeposit(uint256 assets) external view returns (uint256) {
        return convertToShares(assets);
    }

    function deposit(uint256 assets, address receiver) external returns (uint256 shares) {
        shares = convertToShares(assets);
        require(asset.transferFrom(msg.sender, address(this), assets), "transfer failed");
        reserve += assets;
        totalSupply += shares;
        balanceOf[receiver] += shares;
        emit Deposit(msg.sender, receiver, assets, shares);
    }

    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets) {
        require(msg.sender == owner, "not owner");
        assets = convertToAssets(shares);
        balanceOf[owner] -= shares;
        totalSupply -= shares;
        reserve -= assets;
        require(asset.transfer(receiver, assets), "transfer failed");
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }

    function sync() external {
        reserve = asset.balanceOf(address(this));
        emit Sync(reserve);
    }
}
