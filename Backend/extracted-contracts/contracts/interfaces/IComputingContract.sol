// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {ActionParams} from "../libraries/CommonStructs.sol";
interface IComputingContract {
    function getIncreaseLiquidityActions(uint256 _main_token_amount) external view returns (ActionParams[] memory);
    function getDecreaseLiquidityActions(uint256 _main_token_amount) external view returns (ActionParams[] memory);
}
