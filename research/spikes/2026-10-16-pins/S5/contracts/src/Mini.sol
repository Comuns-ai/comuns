// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Mini {
    function info() external view returns (uint256 t, uint256 c) {
        return (block.timestamp, block.chainid);
    }
}
