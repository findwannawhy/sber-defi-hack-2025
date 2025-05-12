// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IChainlinkAggregator {
    function decimals() external view returns (uint8);
}