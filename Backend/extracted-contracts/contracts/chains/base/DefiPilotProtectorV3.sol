// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {AbstractDefiPilotProtectorV3} from "../../abstractContracts/abstractDefiPilotProtectorV3.sol";
import {TokenInfo} from "../../libraries/CommonStructs.sol";

contract DefiPilotProtectorV3 is AbstractDefiPilotProtectorV3 {

    constructor (
        address _pilot_address,
        address _platform_address,
        address _main_token,
        uint256 _max_investment,
        TokenInfo[] memory _tokens,
        uint256 _performance_fee_percent,
        uint256 _commission_fee_proportion,
        uint256 _exit_fee_percent,
        address[] memory _protocol_library_addresses,
        uint256 _max_total_main_token_tvl,
        address _computing_address
    ) AbstractDefiPilotProtectorV3(_pilot_address, _platform_address, _main_token, _max_investment, _tokens, _performance_fee_percent, _commission_fee_proportion, _exit_fee_percent, _protocol_library_addresses, _max_total_main_token_tvl, _computing_address) {
        USDC_FEED_ADDRESS = 0x7e860098F58bBFC8648a4311b374B1D669a2bc6B;
        WETH_PRICE_FEED = 0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70;
    }
}