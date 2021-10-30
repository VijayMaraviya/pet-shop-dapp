# Greets user via a form using POST, a layout, and a single route
import json
from flask import Flask, render_template, request, redirect, url_for
from web3 import Web3


# compile your smart contract with truffle first
with open("./build/contracts/PetShop.json") as f:
    truffleFile = json.load(f)

# web3.py instance
w3 = Web3(Web3.HTTPProvider("http://localhost:7545/"))

abi = truffleFile["abi"]
bytecode = truffleFile["bytecode"]

# set pre-funded account as sender
w3.eth.default_account = w3.eth.accounts[0]

# Instantiate and deploy contract
adopt_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
# Get transaction hash from deployed contract
tx_hash = adopt_contract.constructor(16).transact()
# Get tx receipt
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
# get contract address
contract_address = tx_receipt.contractAddress

# Contract instance in concise mode
deployed_contract = w3.eth.contract(abi=abi, address=contract_address)

accounts = w3.eth.accounts

# load pets data
with open("./static/pets.json") as f:
    PETS_DATA = json.load(f)

# criteria
age = set()
breed = set()
location = set()
for pet in PETS_DATA:
    age.add(pet["age"])
    breed.add(pet["breed"])
    location.add(pet["location"])
criterias = {"age": list(age), "breed": list(breed), "location": list(location)}


def update_criterias():
    for pet in PETS_DATA:
        if pet["age"] not in criterias["age"]:
            criterias["age"].append(pet["age"])
        if pet["location"] not in criterias["location"]:
            criterias["location"].append(pet["location"])


def update_pets_status():
    """
    called after buy or sell to update global data (PETS_DATA)
    """
    contract_data = deployed_contract.functions.getPets().call()

    for pet in PETS_DATA:
        pet["currentOwner"] = contract_data[pet["id"]][1]
        pet["price"] = w3.fromWei(contract_data[pet["id"]][2], "ether")
        pet["isForSell"] = contract_data[pet["id"]][3]


# run once after server starts
update_pets_status()


def filter_data(
    isForSell=None, exclude_owner=None, age_=None, breed_=None, location_=None
):
    """
    Apply filter to global data (PETS_DATA) and return a view
    """
    # without filter
    pets_data = PETS_DATA

    # preprocess
    age = int(age_) if age_ else None
    breed = breed_ if breed_ else None
    location = location_ if location_ else None

    # filter
    if isForSell is not None:
        pets_data = [pet for pet in pets_data if pet["isForSell"] == isForSell]

    if exclude_owner is not None:
        pets_data = [
            pet for pet in pets_data if not pet["currentOwner"] == exclude_owner
        ]

    if age_ is not None:
        pets_data = [pet for pet in pets_data if pet["age"] == age]

    if breed_ is not None:
        pets_data = [pet for pet in pets_data if pet["breed"] == breed]

    if location_ is not None:
        pets_data = [pet for pet in pets_data if pet["location"] == location]

    return pets_data


def get_account_detail(address_):
    balance = w3.fromWei(w3.eth.get_balance(address_), "ether")
    pets = [pet for pet in PETS_DATA if pet["currentOwner"] == address_]
    return (balance, pets)


def handle_buy(buyer, pet_id):
    try:
        # get the price of the pet
        price = deployed_contract.functions.getPrice(int(pet_id)).call()

        # print("price:", price)

        # make transaction from buyer's account
        deployed_contract.functions.buy(int(pet_id)).transact(
            {"from": buyer, "value": price}
        )

        update_pets_status()

        return "success"

    except Exception as e:
        return str(e)


def handle_sell(seller, pet_id, price):
    try:

        # make transaction from seller's account
        deployed_contract.functions.listForSell(
            int(pet_id), w3.toWei(int(price), "ether")
        ).transact({"from": seller})

        update_pets_status()

        return "success"

    except Exception as e:
        return str(e)


def handle_add(owner, price, name, age, breed, location):
    try:

        # make transaction from owner's account
        deployed_contract.functions.addPet(w3.toWei(int(price), "ether")).transact(
            {"from": owner}
        )

        if breed == "French Bulldog":
            breed = "french-bulldog"
        elif breed == "Boxer":
            breed = "boxer"
        elif breed == "Scottish Terrier":
            breed = "scottish-terrier"
        else:
            breed = "golden-retriever"

        new_pet = {
            "id": len(PETS_DATA),
            "name": name,
            "picture": f"images/{breed}.jpeg",
            "age": age,
            "breed": breed,
            "location": location,
        }

        PETS_DATA.append(new_pet)

        update_pets_status()

        update_criterias()

        return "success"

    except Exception as e:
        return str(e)


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    pets_data = filter_data(isForSell=True)

    if request.method == "POST":
        address = request.form.get("account")
        if address:
            return redirect(url_for("account", address=address))
        else:
            age = request.form.get("age")
            breed = request.form.get("breed")
            location = request.form.get("location")

            pets_data = filter_data(
                isForSell=True,
                exclude_owner=None,
                age_=age,
                breed_=breed,
                location_=location,
            )

    return render_template(
        "index.html",
        accounts=accounts,
        criterias=criterias,
        pets=pets_data,
    )


@app.route("/<address>", methods=["GET", "POST"])
def account(address):

    pets_data = filter_data(isForSell=True, exclude_owner=address)
    balance, user_pets = get_account_detail(address)
    user_pets = [pet["name"] for pet in user_pets]

    if request.method == "POST":
        seller = request.form.get("seller")
        List = request.form.get("list")
        Add = request.form.get("add")

        if seller and List == "List":
            return redirect(url_for("seller_info", seller=seller))

        elif seller and Add == "Add":
            return redirect(url_for("add_pet", seller=seller))

        else:
            age = request.form.get("age")
            breed = request.form.get("breed")
            location = request.form.get("location")

            pets_data = filter_data(
                isForSell=True,
                exclude_owner=address,
                age_=age,
                breed_=breed,
                location_=location,
            )

    return render_template(
        "account.html",
        criterias=criterias,
        pets=pets_data,
        user_address=address,
        user_balance=balance,
        user_pets=user_pets,
    )


@app.route("/buy", methods=["GET", "POST"])
def buy():
    if request.method == "POST":
        buyer = request.form.get("buyer")
        pet_id = request.form.get("petID")

        result = handle_buy(buyer, pet_id)

        if result == "success":
            return redirect(url_for("account", address=buyer))

    return result


@app.route("/<seller>/seller_info", methods=["GET", "POST"])
def seller_info(seller):
    balance, user_pets = get_account_detail(seller)

    return render_template(
        "seller.html",
        user_address=seller,
        user_balance=balance,
        user_pets=user_pets,
    )


@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "POST":
        seller = request.form.get("seller")
        pet_id = request.form.get("petID")
        price = request.form.get("price")

        result = handle_sell(seller, pet_id, price)

        if result == "success":
            return redirect(url_for("seller_info", seller=seller))

    return result


@app.route("/<seller>/add_pet", methods=["GET", "POST"])
def add_pet(seller):
    balance, user_pets = get_account_detail(seller)
    user_pets = [pet["name"] for pet in user_pets]

    return render_template(
        "add.html",
        user_address=seller,
        user_balance=balance,
        user_pets=user_pets,
        breeds=criterias["breed"],
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        owner = request.form.get("owner")
        price = request.form.get("price")
        name = request.form.get("name")
        age = request.form.get("age")
        breed = request.form.get("breed")
        location = request.form.get("location")

        result = handle_add(owner, price, name, age, breed, location)

        if result == "success":
            return redirect(url_for("seller_info", seller=owner))

    return result
