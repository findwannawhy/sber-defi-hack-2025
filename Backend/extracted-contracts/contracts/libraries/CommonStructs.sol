// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IUniswapV3Pool} from "../external/interfaces/uniswap/IUniswapV3Pool.sol";
import {IERC20Extended} from "../interfaces/IERC20Extended.sol";

struct PositionDataStruct {
    address token0;
    address token1;
    uint24 fee;
    int24 tick_lower;
    int24 tick_upper;
    uint128 liquidity;
    uint256 fee_growth_inside0_last_x128;
    uint256 fee_growth_inside1_last_x128;
    uint256 tokens_owed0;
    uint256 tokens_owed1;
    IUniswapV3Pool pool;
    int24 current_tick;
    uint160 sqrt_ratio_x96;
}

struct ExplainedBalanceComponent {
    string name;
    uint256 token_value;
    uint256 usd_value;
    uint256 main_token_value;
}

struct TokenInfo {
    IERC20Extended token;
    address price_feed;
    bool is_usd_feed;
    bool is_debt;
}

struct UserHighWaterMark {
    uint256 HWM; // highest wallet balance (in main token)
    uint256 last_update_timestamp;
}

struct ActionParams {
    uint256 protocol_index;
    string function_selector;
    uint256[] uint_params;
    address[] address_params;
    int256[] int_params;
    address token1_to_approve;
    uint256 amount1_to_approve;
    address token2_to_approve;
    uint256 amount2_to_approve;
    uint256 amount1_basis_points;
    uint256 amount2_basis_points;
}

enum StrategyStatusTypes {
    Open,
    Static,
    Closed
}