pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

contract PetShop {
    struct Pet {
        uint256 id;
        address payable currentOwner;
        uint256 price;
        bool isForSell;
    }

    Pet[] public pets;

    constructor(uint256 n) public payable {
        // contract owner
        for (uint256 i = 0; i < n; i++) {
            pets.push(Pet(i, address(uint160(msg.sender)), 2 ether, true));
        }
    }

    // Retrieving the pets
    function getPets() public view returns (Pet[] memory) {
        return pets;
    }

    modifier validateId(uint256 _id) {
        require(_id >= 0 && _id < pets.length, "Invalid ID");
        _;
    }

    modifier validateOwner(uint256 _id, address _owner) {
        require(_id >= 0 && _id < pets.length, "Invalid ID");
        Pet storage pet = pets[_id];
        require(pet.currentOwner == _owner, "Not Owner!");
        _;
    }

    modifier validatePrice(uint256 _price) {
        require(_price >= 0 && _price < 2**256 - 1, "Invaid Price");
        _;
    }

    // Buy a pet
    function buy(uint256 _id) public payable validateId(_id) {
        Pet storage pet = pets[_id];

        // validate status
        require(pet.isForSell == true, "Pet is not for sell");

        // validate price
        require(msg.value >= pet.price, "Insufficient Balance");

        // send ether to current owner
        pet.currentOwner.transfer(msg.value);

        // update sell status
        pet.isForSell = !pet.isForSell;

        // update the price to zero
        pet.price = 0;

        // update the owner
        pet.currentOwner = address(uint160(msg.sender));
    }

    // list a pet for selling
    function listForSell(uint256 _id, uint256 _price)
        public
        validateOwner(_id, msg.sender)
    {
        Pet storage pet = pets[_id];
        if (pet.isForSell != true) {
            pet.isForSell = !pet.isForSell;
        }
        pet.price = _price;
    }

    // add a pet
    function addPet(uint256 _price)
        public
        validatePrice(_price)
        returns (uint256)
    {
        uint256 id = pets.length;
        pets.push(Pet(id, address(uint160(msg.sender)), _price, true));
        return id;
    }

    // get price for a given id
    function getPrice(uint256 _id)
        public
        view
        validateId(_id)
        returns (uint256)
    {
        Pet storage pet = pets[_id];
        uint256 price = pet.price;
        return price;
    }

    // get the owner for a given pet
    function getOwner(uint256 _id)
        public
        view
        validateId(_id)
        returns (address)
    {
        Pet storage pet = pets[_id];
        address owner = pet.currentOwner;
        return owner;
    }
}
