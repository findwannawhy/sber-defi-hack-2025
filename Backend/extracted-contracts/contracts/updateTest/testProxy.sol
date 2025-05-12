// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestProxy {
    address public owner;
    address public implementation;

    event Upgraded(address indexed implementation);

    constructor() {
        owner = msg.sender;
    }

    function newImplementation(address _newImplementation) external {
        require(msg.sender == owner, "Only owner can call this function");
        implementation = _newImplementation;
        emit Upgraded(_newImplementation);
    }
}
