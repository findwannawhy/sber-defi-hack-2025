// SPDX-License-Identifier: MIT
// Compatible with OpenZeppelin Contracts ^5.0.0
pragma solidity ^0.8.0;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract DefiPilotLpToken is ERC20, ERC20Burnable, Ownable {

    uint8 private _decimals;

    constructor(string memory _name, string memory _symbol, uint8 _inheritableDecimals, address _initialOwner)
        ERC20(_name, _symbol)
        Ownable(_initialOwner)
    {
        _decimals = _inheritableDecimals;
    }

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    function burnFrom(address account, uint256 value) public override onlyOwner {
        _burn(account, value);    
    }

    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }
}
