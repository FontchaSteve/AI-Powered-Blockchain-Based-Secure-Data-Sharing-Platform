from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

def get_web3():
    """Connect to local Ganache"""
    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    w3 = Web3(Web3.HTTPProvider(ganache_url))
    
    if w3.is_connected():
        print(f"✅ Successfully connected to Ganache at {ganache_url}")
        print(f"Current block: {w3.eth.block_number}")
        print(f"Accounts available: {len(w3.eth.accounts)}")
    else:
        print("❌ Failed to connect to Ganache. Make sure Ganache is running!")
    
    return w3

# Test connection
if __name__ == "__main__":
    get_web3()