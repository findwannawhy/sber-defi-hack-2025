// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {DefiPilotLpToken} from "../DefiPilotLpToken.sol";
import {IAggregatorV3Interface} from "../interfaces/IAggregatorV3Interface.sol";
import {IERC20Extended} from "../interfaces/IERC20Extended.sol";
import {BokkyPooBahsDateTimeLibrary} from "../external/libraries/BokkyPooBahsDateTimeLibrary.sol";
import {IComputingContract} from "../interfaces/IComputingContract.sol";
import {ExplainedBalanceComponent, TokenInfo, UserHighWaterMark, ActionParams, StrategyStatusTypes} from "../libraries/CommonStructs.sol";
import {IBaseChecker} from "../interfaces/IBaseChecker.sol";
import {IChainlinkAggregator} from "../interfaces/IChainlinkAggregator.sol";
import {IPermit2} from "@uniswap/permit2/src/interfaces/IPermit2.sol";
import {IUniversalRouter} from "@uniswap/universal-router/contracts/interfaces/IUniversalRouter.sol";
import {BaseStorage} from "./baseStorage.sol";

abstract contract AbstractDefiPilotProtectorV3 {
    using BokkyPooBahsDateTimeLibrary for uint256;

    modifier only_pilot_or_platform() {
        require(msg.sender == pilot_address || msg.sender == platform_address, "Not pilot or platform");
        _;
    }

    modifier not_closed() {
        require(strategy_status != StrategyStatusTypes.Closed, "Strategy closed");
        _;
    }

    address public immutable USDC_FEED_ADDRESS;
    address public immutable WETH_PRICE_FEED;

    DefiPilotLpToken public defi_pilot_lp_token;
    IERC20Extended public main_token;
    uint256 public max_investment;
    uint256 public max_total_main_token_tvl;

    mapping(address => uint256) public waiting_for_withdraw_amount_lp_dfp;
    mapping(bytes32 => bytes) private storageData;

    uint256 public constant MAX_PRICEFEEDS_DELAY = 2 days;

    uint256 public constant PERFORMANCE_COMMISSION_DAYS_SLIPPAGE = 10;
    mapping(address => UserHighWaterMark) public hwm_registry;

    uint256 public constant discount_factor_scale = 1e27;

    uint256 public constant fee_scale = 10000;
    uint256 public immutable performance_fee; // commission for results

    uint256 public immutable commission_fee_proportion; // how much percentage should a pilot receive

    uint256 public immutable exit_fee; // commission for exit

    uint256 public constant amount_basis_points_scale = 10000;

    address public platform_address;
    address public pilot_address;

    address public computing_address;

    mapping(address => uint256) public change_pilot_signatures;
    mapping(address => uint256) public change_platform_signatures;

    StrategyStatusTypes public strategy_status;

    TokenInfo[] public token_info_array;

    address[] public protocol_library_addresses;
    mapping(uint256 => address) public protocol_library_allowed;

    constructor(
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
    ) {
        require(_main_token != address(0), "Invalid main token");
        require(_tokens.length > 0, "Invalid tokens array");
        require(address(_tokens[0].token) == _main_token, "Invalid main token");
        for (uint256 i; i < _tokens.length; i++) {
            require(address(_tokens[i].token) != address(0), "Invalid token address");
            require(_tokens[i].price_feed != address(0), "Invalid price feed address");
            if (address(_tokens[i].price_feed) != USDC_FEED_ADDRESS) {
                IAggregatorV3Interface price_feed = IAggregatorV3Interface(_tokens[i].price_feed);
                (, , , uint256 updated_at, ) = price_feed.latestRoundData();
                require(block.timestamp - updated_at <= MAX_PRICEFEEDS_DELAY, "Invalid price feed address");
            }
        }

        strategy_status = StrategyStatusTypes.Open;

        platform_address = _platform_address;
        pilot_address = _pilot_address;

        computing_address = _computing_address;
        protocol_library_addresses = _protocol_library_addresses;
        for (uint256 i; i < _protocol_library_addresses.length; i++) {
            protocol_library_allowed[i] = _protocol_library_addresses[i];
        }

        performance_fee = _performance_fee_percent;
        commission_fee_proportion = _commission_fee_proportion;
        exit_fee = _exit_fee_percent;

        string memory defi_pilot_lp_token_name = _createTokenName("DeFi Pilot Token ", _main_token);
        string memory defi_pilot_lp_token_symbol = _createTokenName("dfp", _main_token);

        uint8 decimals = IERC20Extended(_main_token).decimals();
        defi_pilot_lp_token = new DefiPilotLpToken(defi_pilot_lp_token_name, defi_pilot_lp_token_symbol, decimals, address(this));
        main_token = IERC20Extended(_main_token);
        max_investment = _max_investment;
        max_total_main_token_tvl = _max_total_main_token_tvl;
        token_info_array = _tokens;
    }

    function enterStrategy(uint256 _main_token_amount) external not_closed {
        require(_main_token_amount > 0, "Amount must be greater than zero");
        uint256 user_dfp_balance = defi_pilot_lp_token.balanceOf(msg.sender);
        uint256 current_discount_factor = getDiscountFactor();
        require(
            ((user_dfp_balance * current_discount_factor) / discount_factor_scale + _main_token_amount) <= max_investment || msg.sender == pilot_address,
            "More than max investment"
        );
        require(
            getMainTokenTotalBalance() + _main_token_amount <= max_total_main_token_tvl || msg.sender == pilot_address,
            "Max total main token TVL exceeded"
        );
        defi_pilot_lp_token.mint(msg.sender, (_main_token_amount * discount_factor_scale) / current_discount_factor);
        require(main_token.transferFrom(msg.sender, address(this), _main_token_amount), "Transfer failed");
        if (msg.sender != pilot_address) {
            hwm_registry[msg.sender].HWM += _main_token_amount;
        }
        if (computing_address != address(0) && msg.sender != pilot_address) {
            ActionParams[] memory actions = IComputingContract(computing_address).getIncreaseLiquidityActions(
                (_main_token_amount * discount_factor_scale) / current_discount_factor
            );
            _performMultipleActions(actions);
        }
    }

    function exitStrategy(uint256 _lp_dfp_amount) external {
        require(_lp_dfp_amount > 0, "Amount must be greater than zero");
        require(defi_pilot_lp_token.balanceOf(msg.sender) >= _lp_dfp_amount, "Insufficient balance");
        uint256 current_discount_factor = getDiscountFactor();
        if (main_token.balanceOf(address(this)) < (_lp_dfp_amount * current_discount_factor) / discount_factor_scale && computing_address == address(0)) {
            waiting_for_withdraw_amount_lp_dfp[msg.sender] = _lp_dfp_amount;
        } else {
            if (computing_address != address(0) && main_token.balanceOf(address(this)) < (_lp_dfp_amount * current_discount_factor) / discount_factor_scale) {
                ActionParams[] memory actions = IComputingContract(computing_address).getDecreaseLiquidityActions(_lp_dfp_amount);
                _performMultipleActions(actions);
            }
            current_discount_factor = getDiscountFactor();
            if (msg.sender != pilot_address && msg.sender != platform_address) {
                uint256 user_performance_fee = _calculatePerformanceFee(msg.sender, _lp_dfp_amount, current_discount_factor);
                uint256 user_exit_fee = ((_lp_dfp_amount - user_performance_fee) * exit_fee) / fee_scale;
                main_token.transfer(msg.sender, ((_lp_dfp_amount - user_performance_fee - user_exit_fee) * current_discount_factor) / discount_factor_scale);
                defi_pilot_lp_token.mint(pilot_address, (user_performance_fee * commission_fee_proportion) / fee_scale);
                defi_pilot_lp_token.mint(platform_address, (user_performance_fee * (fee_scale - commission_fee_proportion)) / fee_scale + user_exit_fee);
            } else {
                main_token.transfer(msg.sender, (_lp_dfp_amount * current_discount_factor) / discount_factor_scale);
            }
            defi_pilot_lp_token.burnFrom(msg.sender, _lp_dfp_amount);
        }
    }

    function exitStrategyAfterWaiting(address _user_address, uint256 _lp_dfp_amount) external only_pilot_or_platform {
        uint256 current_discount_factor = getDiscountFactor();
        require(main_token.balanceOf(address(this)) >= (_lp_dfp_amount * current_discount_factor) / discount_factor_scale, "Insufficient balance");
        require(waiting_for_withdraw_amount_lp_dfp[_user_address] == _lp_dfp_amount, "Invalid amount");
        if (msg.sender != pilot_address && msg.sender != platform_address) {
            uint256 user_performance_fee = _calculatePerformanceFee(_user_address, _lp_dfp_amount, current_discount_factor);
            uint256 user_exit_fee = ((_lp_dfp_amount - user_performance_fee) * exit_fee) / fee_scale;
            main_token.transfer(_user_address, ((_lp_dfp_amount - user_performance_fee - user_exit_fee) * current_discount_factor) / discount_factor_scale);
            defi_pilot_lp_token.mint(pilot_address, (user_performance_fee * commission_fee_proportion) / fee_scale);
            defi_pilot_lp_token.mint(platform_address, (user_performance_fee * (fee_scale - commission_fee_proportion)) / fee_scale + user_exit_fee);
        } else {
            main_token.transfer(_user_address, (_lp_dfp_amount * current_discount_factor) / discount_factor_scale);
        }
        defi_pilot_lp_token.burnFrom(_user_address, _lp_dfp_amount);
        waiting_for_withdraw_amount_lp_dfp[_user_address] = 0;
    }

    function _calculatePerformanceFee(address _user_address, uint256 _lp_dfp_amount, uint256 current_discount_factor) internal returns (uint256) {
        uint256 user_balance = defi_pilot_lp_token.balanceOf(_user_address);
        uint256 nav = (user_balance * current_discount_factor) / discount_factor_scale;
        uint256 hwm = hwm_registry[_user_address].HWM;
        if (nav > hwm) {
            hwm_registry[_user_address].HWM = nav - (_lp_dfp_amount * current_discount_factor) / discount_factor_scale;
            return ((nav - hwm) * performance_fee * discount_factor_scale * _lp_dfp_amount) / current_discount_factor / fee_scale / user_balance;
        }
        return 0;
    }

    function performAction(
        uint256 _protocol_index,
        string memory _function_selector,
        uint256[] memory _uint_params,
        int256[] memory _int_params,
        address[] memory _address_params,
        address _token1_to_approve, //if protocol needs 1 or 0 approvals set _token1_to_approve and _amount1_to_approve to 0
        uint256 _amount1_to_approve,
        address _token2_to_approve,
        uint256 _amount2_to_approve,
        uint256 _amount1_basis_points,
        uint256 _amount2_basis_points
    ) external only_pilot_or_platform {
        _performAction(
            _protocol_index,
            _function_selector,
            _uint_params,
            _int_params,
            _address_params,
            _token1_to_approve,
            _amount1_to_approve,
            _token2_to_approve,
            _amount2_to_approve,
            _amount1_basis_points,
            _amount2_basis_points
        );
    }

    function _performAction(
        uint256 _protocol_index,
        string memory _function_selector,
        uint256[] memory _uint_params,
        int256[] memory _int_params,
        address[] memory _address_params,
        address _token1_to_approve,
        uint256 _amount1_to_approve,
        address _token2_to_approve,
        uint256 _amount2_to_approve,
        uint256 _amount1_basis_points,
        uint256 _amount2_basis_points
    ) internal {
        require(protocol_library_allowed[_protocol_index] != address(0), "Invalid protocol");
        (bytes memory call_data, bytes32 local_storage_key, bytes memory local_storage_data) = IBaseChecker(protocol_library_allowed[_protocol_index]).getPerformActionData(
            _function_selector,
            _uint_params,
            _int_params,
            _address_params,
            _amount1_basis_points,
            _amount2_basis_points
        );
        if (local_storage_key != bytes32(0)) {
            _setStorageValue(local_storage_key, local_storage_data);
        }
        bool is_permit2 = IBaseChecker(protocol_library_allowed[_protocol_index]).PERMIT2() != address(0);
        _approveTokens(_token1_to_approve, _amount1_to_approve, _token2_to_approve, _amount2_to_approve, protocol_library_allowed[_protocol_index], is_permit2);
        (bool success, ) = IBaseChecker(protocol_library_allowed[_protocol_index]).PROTOCOL_ADDRESS().call(call_data);
        require(success, "Call failed");
    }

    function performMultipleActions(ActionParams[] calldata actions) external only_pilot_or_platform {
        _performMultipleActions(actions);
    }

    function _performMultipleActions(ActionParams[] memory actions) internal {
        for (uint256 i; i < actions.length; i++) {
            _performAction(
                actions[i].protocol_index,
                actions[i].function_selector,
                actions[i].uint_params,
                actions[i].int_params,
                actions[i].address_params,
                actions[i].token1_to_approve,
                actions[i].amount1_to_approve,
                actions[i].token2_to_approve,
                actions[i].amount2_to_approve,
                actions[i].amount1_basis_points,
                actions[i].amount2_basis_points
            );
        }
    }

    function _approveTokens(address _token1, uint256 _amount1, address _token2, uint256 _amount2, address _protocol, bool _is_permit2) internal {
        if (_is_permit2) {
            if (_token1 != address(0)) {
                _approveTokenWithPermit2(
                    _token1,
                    uint128(_amount1),
                    uint48(block.timestamp + 1 minutes),
                    IBaseChecker(_protocol).PERMIT2(),
                    IBaseChecker(_protocol).PROTOCOL_ADDRESS()
                );
            }
            if (_token2 != address(0)) {
                _approveTokenWithPermit2(
                    _token2,
                    uint128(_amount2),
                    uint48(block.timestamp + 1 minutes),
                    IBaseChecker(_protocol).PERMIT2(),
                    IBaseChecker(_protocol).PROTOCOL_ADDRESS()
                );
            }
        } else {
            if (_token1 != address(0)) {
                require(IERC20(_token1).approve(IBaseChecker(_protocol).PROTOCOL_ADDRESS(), _amount1), "Approve failed");
            }
            if (_token2 != address(0)) {
                require(IERC20(_token2).approve(IBaseChecker(_protocol).PROTOCOL_ADDRESS(), _amount2), "Approve failed");
            }
        }
    }

    function _approveTokenWithPermit2(address token, uint128 amount, uint48 expiration, address permit2, address router) internal {
        IERC20(token).approve(permit2, type(uint256).max);
        IPermit2(permit2).approve(token, router, uint160(amount), expiration);
    }

    function getMainTokenTotalBalance() public view returns (uint256 total_main_token_balance) {
        //todo проверить
        for (uint256 i; i < token_info_array.length; i++) {
            total_main_token_balance += _calculateFromTo(token_info_array[i].token.balanceOf(address(this)), token_info_array[i].token, main_token);
        }
        for (uint256 i; i < protocol_library_addresses.length; i++) {
            total_main_token_balance += IBaseChecker(protocol_library_addresses[i]).getMainTokenTotalBalance(token_info_array[0]);
        }
    }

    function getTotalBalanceExplained() external view returns (ExplainedBalanceComponent[] memory) {
        //todo починить
        ExplainedBalanceComponent[] memory components;
        uint256 totalComponents = 0;

        for (uint256 i; i < protocol_library_addresses.length; i++) {
            ExplainedBalanceComponent[] memory currentComponents = IBaseChecker(protocol_library_addresses[i]).getTotalBalanceExplained(token_info_array[0]);
            totalComponents += currentComponents.length;
        }

        components = new ExplainedBalanceComponent[](totalComponents + token_info_array.length);
        uint256 currentIndex = 0;

        for (uint256 i; i < protocol_library_addresses.length; i++) {
            ExplainedBalanceComponent[] memory currentComponents = IBaseChecker(protocol_library_addresses[i]).getTotalBalanceExplained(token_info_array[0]);
            for (uint256 j = 0; j < currentComponents.length; j++) {
                components[currentIndex] = currentComponents[j];
                currentIndex++;
            }
        }

        for (uint256 i; i < token_info_array.length; i++) {
            string memory token_name = string(abi.encodePacked(token_info_array[i].token.symbol(), "_balance"));
            components[currentIndex] = ExplainedBalanceComponent(
                token_name,
                token_info_array[i].token.balanceOf(address(this)),
                _convertTokenToUsd(token_info_array[i].token.balanceOf(address(this)), token_info_array[i].token),
                _calculateFromTo(token_info_array[i].token.balanceOf(address(this)), token_info_array[i].token, main_token)
            );
            currentIndex++;
        }

        return components;
    }

    function calculateMonthlyPerformanceFees(address[] memory _user_addresses) external {
        uint256 total_comission;
        uint256 current_discount_factor = getDiscountFactor();
        for (uint256 i; i < _user_addresses.length; i++) {
            require(_checkTimestamp(hwm_registry[_user_addresses[i]].last_update_timestamp), "Cannot update HWM");
            uint256 HWM = hwm_registry[_user_addresses[i]].HWM; //HWM - high water mark (highest user balance value)
            uint256 NAV = (defi_pilot_lp_token.balanceOf(_user_addresses[i]) * current_discount_factor) / discount_factor_scale; //Net Asset Value
            if (NAV > HWM) {
                uint256 performance_fee_in_defi_pilot_lp_token = ((NAV - HWM) * performance_fee * discount_factor_scale) / current_discount_factor / fee_scale;
                defi_pilot_lp_token.burnFrom(_user_addresses[i], performance_fee_in_defi_pilot_lp_token);
                total_comission += performance_fee_in_defi_pilot_lp_token;
                hwm_registry[_user_addresses[i]].HWM = NAV;
            }
            hwm_registry[_user_addresses[i]].last_update_timestamp = block.timestamp;
        }
        defi_pilot_lp_token.mint(pilot_address, (total_comission * commission_fee_proportion) / fee_scale);
        defi_pilot_lp_token.mint(platform_address, (total_comission * (fee_scale - commission_fee_proportion)) / fee_scale);
    }

    //check that the old and new timestamp differ by more than 10 days, also check that today's date is between the 1st and 10th
    function _checkTimestamp(uint256 _last_update_timestamp) internal view returns (bool) {
        uint256 current_timestamp = block.timestamp;
        (, , uint256 current_day) = current_timestamp.timestampToDate();
        return
            (_last_update_timestamp / 1 days + PERFORMANCE_COMMISSION_DAYS_SLIPPAGE < current_timestamp / 1 days) &&
            (1 <= current_day && current_day <= PERFORMANCE_COMMISSION_DAYS_SLIPPAGE);
    }

    function _uintToString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }

    function getDiscountFactor() public view returns (uint256) {
        uint256 total_supply = defi_pilot_lp_token.totalSupply();
        if (total_supply > 0) {
            return (discount_factor_scale * getMainTokenTotalBalance()) / total_supply;
        }
        return discount_factor_scale;
    }

    function _createTokenName(string memory base_name, address _token) internal view returns (string memory) {
        return string(abi.encodePacked(base_name, IERC20Extended(_token).symbol(), "-", _uintToString(block.timestamp)));
    }

    function changeRole(address _new_address, uint256 _signature_expires_at, bool is_pilot_confirmation) external only_pilot_or_platform {
        bool is_sender_pilot = msg.sender == pilot_address;
        if ((is_pilot_confirmation && is_sender_pilot) || (!is_pilot_confirmation && !is_sender_pilot)) {
            if (_signature_expires_at == 0) {
                _signature_expires_at = block.timestamp + 10 minutes;
            }
            if (is_pilot_confirmation) {
                change_pilot_signatures[_new_address] = _signature_expires_at;
            } else {
                require(_new_address != address(0), "Invalid address");
                change_platform_signatures[_new_address] = _signature_expires_at;
            }
        } else {
            if (is_pilot_confirmation) {
                require(change_pilot_signatures[_new_address] > block.timestamp, "Outdated address");
                if (_new_address == address(0)) {
                    strategy_status = getMainTokenTotalBalance() == main_token.balanceOf(address(this))
                        ? StrategyStatusTypes.Static
                        : StrategyStatusTypes.Closed;
                } else {
                    _changeLpTokensOwner(pilot_address, _new_address);
                }
                pilot_address = _new_address;
            } else {
                require(change_platform_signatures[_new_address] > block.timestamp, "Outdated address");
                _changeLpTokensOwner(platform_address, _new_address);
                platform_address = _new_address;
            }
        }
    }

    function _changeLpTokensOwner(address _old_owner, address _new_owner) internal {
        defi_pilot_lp_token.mint(_new_owner, defi_pilot_lp_token.balanceOf(_old_owner));
        defi_pilot_lp_token.burnFrom(_old_owner, defi_pilot_lp_token.balanceOf(_old_owner));
    }

    function setComputingAddress(address _computing_address) external only_pilot_or_platform {
        computing_address = _computing_address;
    }

    function _calculateFromTo(uint256 _amount, IERC20Extended _token1, IERC20Extended _token2) public view returns (uint256) {
        IChainlinkAggregator price_feed_token1;
        IChainlinkAggregator price_feed_token2;

        if (!_checkIsUsdFeed(address(_token1))) {
            _amount = _calculateThroughEth(_amount, _token1, true);
            price_feed_token1 = IChainlinkAggregator(WETH_PRICE_FEED);
        } else {
            price_feed_token1 = IChainlinkAggregator(_getTokenFeed(address(_token1)));
        }

        if (!_checkIsUsdFeed(address(_token2))) {
            price_feed_token2 = IChainlinkAggregator(WETH_PRICE_FEED);
        } else {
            price_feed_token2 = IChainlinkAggregator(_getTokenFeed(address(_token2)));
        }

        uint8 feed1_decimals = price_feed_token1.decimals();
        uint8 feed2_decimals = price_feed_token2.decimals();

        uint8 token1_decimals = _token1.decimals();
        uint8 token2_decimals = _token2.decimals();

        uint256 scale_numerator = 10 ** (uint256(feed2_decimals) + uint256(token2_decimals));
        uint256 scale_denom = 10 ** (uint256(feed1_decimals) + uint256(token1_decimals));

        uint256 token2_amount = (_amount * uint256(_getTokenPrice(address(price_feed_token1))) * scale_numerator) /
            (uint256(_getTokenPrice(address(price_feed_token2))) * scale_denom);

        if (!_checkIsUsdFeed(address(_token2))) {
            return _calculateThroughEth(token2_amount, _token2, false);
        } else {
            return token2_amount;
        }
    }

    function _getTokenFeed(address _token_address) internal view returns (address price_feed) {
        for (uint256 j; j < token_info_array.length; j++) {
            if (_token_address == address(token_info_array[j].token)) {
                return token_info_array[j].price_feed;
            }
        }
    }

    function _checkIsUsdFeed(address _token_address) internal view returns (bool is_usd_feed) {
        for (uint256 j; j < token_info_array.length; j++) {
            if (_token_address == address(token_info_array[j].token)) {
                return token_info_array[j].is_usd_feed;
            }
        }
    }

    function _calculateThroughEth(uint256 _amount, IERC20Extended _token, bool _is_calculate_to_token) internal view returns (uint256) {
        IChainlinkAggregator price_feed = IChainlinkAggregator(_getTokenFeed(address(_token)));
        uint8 feed_decimals = price_feed.decimals();
        uint256 token_price = uint256(_getTokenPrice(address(price_feed)));
        if (_is_calculate_to_token) {
            return (_amount * token_price) / (10 ** feed_decimals);
        } else {
            return (_amount * (10 ** feed_decimals)) / token_price;
        }
    }

    function _getTokenPrice(address _price_feed) internal view returns (uint256) {
        IAggregatorV3Interface price_feed = IAggregatorV3Interface(_price_feed);
        (, int256 price, , , ) = price_feed.latestRoundData();
        return uint256(price);
    }

    function _convertTokenToUsd(uint256 _amount, IERC20Extended _token) internal view returns (uint256) {
        // calculate from token to usd
        IChainlinkAggregator price_feed;

        if (!_checkIsUsdFeed(address(_token))) {
            _amount = _calculateThroughEth(_amount, _token, true);
            price_feed = IChainlinkAggregator(WETH_PRICE_FEED);
        } else {
            price_feed = IChainlinkAggregator(_getTokenFeed(address(_token)));
        }

        uint256 token_price = uint256(_getTokenPrice(address(price_feed)));

        uint8 feed_decimals = price_feed.decimals();
        uint8 token_decimals = _token.decimals();

        uint256 usd_value = (_amount * token_price * (10 ** 6)) / (10 ** (uint256(token_decimals) + uint256(feed_decimals)));

        return usd_value;
    }

    function setCheckersAddresses(address[] memory _protocol_library_addresses) external only_pilot_or_platform {
        protocol_library_addresses = _protocol_library_addresses; //todo УДАЛИТЬ ПОСЛЕ ТЕСТИРОВАНИЯ!!!!!!
        for (uint256 i; i < protocol_library_addresses.length; i++) {
            protocol_library_allowed[i] = protocol_library_addresses[i];
        }
    }

    function isLibraryAvailable(uint256 _library_index) external view returns (bool) {
        return protocol_library_addresses[_library_index] != address(0);
    }

    function _setStorageValue(bytes32 key, bytes memory value) internal {
        storageData[key] = value;
    }

    function getStorageValue(bytes32 key) public view returns (bytes memory) {
        return storageData[key];
    }
}
