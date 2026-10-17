// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;
contract V {
    struct Voucher { bytes32 sessionId; uint64 seq; uint256 cumulativeWei; uint64 inputTokens; uint64 outputTokens; bytes32 outputCommitment; bool final; }
}
