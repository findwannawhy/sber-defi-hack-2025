// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {TokenInfo, ExplainedBalanceComponent} from "../libraries/CommonStructs.sol";
import {IERC20Extended} from "./IERC20Extended.sol";
interface IBaseChecker {
    function PROTOCOL_ADDRESS() external view returns (address);
    function PERMIT2() external view returns (address);
    
    function getPerformActionData(
        string memory _function_selector,
        uint256[] memory _uint_params,
        int256[] memory _int_params,
        address[] memory _address_params,
        uint256 _amount1_basis_points,
        uint256 _amount2_basis_points
    ) external returns (bytes memory, bytes32, bytes memory);

    function _isAllowedToken(
        address _token_address,
        TokenInfo[] memory token_info_array
    ) external pure returns (bool);

    function _createCallData(
        string memory _function_selector,
        bytes memory _encoded_data
    ) external pure returns (bytes memory);

    function _getAmountByBasisPoints(
        address _asset,
        uint256 _basis_points,
        uint256 _amount,
        uint256 amount_basis_points_scale
    ) external view returns (uint256);

    function getMainTokenTotalBalance(TokenInfo calldata _main_token) external view returns (uint256);

    function getTotalBalanceExplained(TokenInfo calldata _main_token) external view returns (ExplainedBalanceComponent[] memory);
}
