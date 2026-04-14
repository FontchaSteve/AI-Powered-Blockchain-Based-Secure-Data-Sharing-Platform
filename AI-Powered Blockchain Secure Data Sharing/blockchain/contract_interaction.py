from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Always resolve relative to THIS file's directory — safe regardless of cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACT_INFO_PATH = os.path.join(BASE_DIR, 'contract_info.json')

CONTRACT_ADDRESS = "0x4f73Ca23AEEAfd4f6c63d6A5EC644aA77F71faF4"


def get_web3():
    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    return Web3(Web3.HTTPProvider(ganache_url))


def get_contract():
    """Return (w3, contract) tuple. Raises clearly if Ganache is not running."""
    w3 = get_web3()

    if not w3.is_connected():
        raise ConnectionError(
            "Cannot connect to Ganache. Make sure Ganache is running at "
            + os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
        )

    with open(CONTRACT_INFO_PATH, 'r') as f:
        contract_data = json.load(f)

    contract = w3.eth.contract(
        address=CONTRACT_ADDRESS,
        abi=contract_data['abi'],
    )

    return w3, contract


# Quick test
if __name__ == "__main__":
    w3, contract = get_contract()
    print("✅ Contract loaded successfully!")
    print(f"Contract Address: {CONTRACT_ADDRESS}")
    print(f"Current Block: {w3.eth.block_number}")