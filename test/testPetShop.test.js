const PetShop = artifacts.require("PetShop");

contract("PetShop", (accounts) => {
    let petshop;
    let expectedBuyer;
    let expectedSeller;
    let expectedPrice;

    before(async () => {
        petshop = await PetShop.deployed();
    });

    describe("Buying a pet and retrieving account addresses", async () => {
        before("Buy a pet using accounts[1]", async () => {
            await petshop.buy(8, { from: accounts[1], value: 2000000000000000000 });
            expectedBuyer = accounts[1];
        });

        it("can fetch the address of an owner by pet id", async () => {
            const owner = await petshop.getOwner(8);
            assert.equal(owner, expectedBuyer, "The owner of the pet should be the second account.");
        });

        it("can fetch the collection of all pets", async () => {
            const pets = await petshop.getPets();
            assert.equal(pets[8].currentOwner, expectedBuyer, "The owner of the pet should be in the collection.");
        })
    });

    describe("List a pet for selling and retrieving price", async () => {
        before("List a pet using accounts[1]", async () => {
            await petshop.listForSell(8, "1000000000000000000", { from: accounts[1] });
            expectedPrice = "1000000000000000000";
            expectedSeller = accounts[1]
        });

        it("can fetch the price of an pet set by owner", async () => {
            const price = await petshop.getPrice(8);
            assert.equal(price, expectedPrice, "The price of the pet should equal to the amount set by seller.");
        });

        it("can fetch the collection of all pets and get the status", async () => {
            const pets = await petshop.getPets();
            assert.equal(pets[8].isForSell, true, "The pet should be listed for selling.");
        })
    });

    describe("Buying a listed pet from the seller and checking the deposit", async () => {
        before("Buy a pet using another account: accounts[3]", async () => {
            oldBalance = await web3.eth.getBalance(accounts[1]);
            await petshop.buy(8, { from: accounts[3], value: "1000000000000000000" });
        });

        it("can fetch the account balance of the owner (account[1]) and verify deposit", async () => {
            newBalance = await web3.eth.getBalance(accounts[1]);
            assert.equal(parseInt(newBalance), parseInt(oldBalance) + parseInt(expectedPrice), "The owner should recieve the listed price.");
        });

        it("can check the status of the sold pet", async () => {
            const pets = await petshop.getPets();
            assert.equal(pets[8].isForSell, false, "The sold pet should change the status 'isForSell' to false.");
        })

        it("can fetch the address of new owner by pet id", async () => {
            const newOwner = await petshop.getOwner(8);
            assert.equal(newOwner, accounts[3], "The owner of the pet should be the fourth account.");
        });
    });
});