// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BaseStorage {
    mapping(bytes32 => bytes) private storageData;

    function setStorageValue(bytes32 key, bytes calldata value) public {
        storageData[key] = value;
    }

    function getStorageValue(bytes32 key) public view returns (bytes memory) {
        return storageData[key];
    }

    function deleteStorageValue(bytes32 key) public {
        delete storageData[key];
    }
}
