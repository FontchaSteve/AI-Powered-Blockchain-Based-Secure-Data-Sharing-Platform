// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SecureShare {
    address public owner;

    struct File {
        string fileHash;        // IPFS hash or SHA256 hash of the encrypted file
        address owner;
        uint256 uploadTime;
        bool isActive;
    }

    struct AccessPermission {
        address user;
        uint256 expirationTime;
        bool canRead;
        bool canWrite;
    }

    // Mappings
    mapping(string => File) public files;                    // fileHash => File
    mapping(string => mapping(address => AccessPermission)) public permissions; // fileHash => user => permission

    // Events (these will be logged and can be read by Django + AI)
    event FileUploaded(string fileHash, address owner, uint256 timestamp);
    event AccessGranted(string fileHash, address user, uint256 expirationTime);
    event AccessRevoked(string fileHash, address user);
    event FileAccessed(string fileHash, address user, uint256 timestamp);

    constructor() {
        owner = msg.sender;
    }

    // Upload file hash to blockchain
    function uploadFile(string memory _fileHash) public {
        require(bytes(_fileHash).length > 0, "File hash cannot be empty");
        
        files[_fileHash] = File({
            fileHash: _fileHash,
            owner: msg.sender,
            uploadTime: block.timestamp,
            isActive: true
        });

        emit FileUploaded(_fileHash, msg.sender, block.timestamp);
    }

    // Grant access to a user
    function grantAccess(
        string memory _fileHash,
        address _user,
        uint256 _expirationTime
    ) public {
        File memory file = files[_fileHash];
        require(file.owner == msg.sender, "Only file owner can grant access");
        require(file.isActive, "File is not active");

        permissions[_fileHash][_user] = AccessPermission({
            user: _user,
            expirationTime: _expirationTime,
            canRead: true,
            canWrite: false
        });

        emit AccessGranted(_fileHash, _user, _expirationTime);
    }

    // Revoke access
    function revokeAccess(string memory _fileHash, address _user) public {
        File memory file = files[_fileHash];
        require(file.owner == msg.sender, "Only file owner can revoke access");

        delete permissions[_fileHash][_user];
        emit AccessRevoked(_fileHash, _user);
    }

    // Record when someone accesses the file (for AI monitoring)
    function recordAccess(string memory _fileHash) public {
        require(files[_fileHash].isActive, "File is not active");
        
        // Check if user has permission
        AccessPermission memory perm = permissions[_fileHash][msg.sender];
        require(perm.canRead, "No read permission");
        require(block.timestamp <= perm.expirationTime, "Access expired");

        emit FileAccessed(_fileHash, msg.sender, block.timestamp);
    }

    // Check if user has active permission
    function hasAccess(string memory _fileHash, address _user) public view returns (bool) {
        AccessPermission memory perm = permissions[_fileHash][_user];
        return perm.canRead && block.timestamp <= perm.expirationTime;
    }

    // Get file owner
    function getFileOwner(string memory _fileHash) public view returns (address) {
        return files[_fileHash].owner;
    }
}