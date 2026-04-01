from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()

CONTRACT_ADDRESS = "0x4f73Ca23AEEAfd4f6c63d6A5EC644aA77F71faF4"

def get_web3():
    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    return Web3(Web3.HTTPProvider(ganache_url))

def get_contract():
    """Return both w3 and contract - FIXED"""
    w3 = get_web3()
    
    # Load ABI
    with open('blockchain/contract_info.json', 'r') as f:
        contract_data = json.load(f)
    
    contract = w3.eth.contract(
        address=CONTRACT_ADDRESS,
        abi=contract_data['abi']
    )
    
    return w3, contract   # ← This must return TWO values

# Quick test
if __name__ == "__main__":
    w3, contract = get_contract()
    print("✅ Contract loaded successfully!")
    print(f"Contract Address: {CONTRACT_ADDRESS}")
    print(f"Current Block: {w3.eth.block_number}")