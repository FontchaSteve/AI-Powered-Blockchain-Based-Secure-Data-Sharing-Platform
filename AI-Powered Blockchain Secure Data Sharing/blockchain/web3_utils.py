from web3 import Web3
from dotenv import load_dotenv
import os
import json
from solcx import compile_source, install_solc

load_dotenv()

# Install Solidity compiler if needed (run once)
try:
    install_solc('0.8.20')
except:
    pass

def get_web3():
    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    w3 = Web3(Web3.HTTPProvider(ganache_url))
    
    if w3.is_connected():
        print("✅ Connected to Ganache")
        print(f"URL: {ganache_url}")
        print(f"Accounts available: {len(w3.eth.accounts)}")
        return w3
    else:
        print("❌ Failed to connect to Ganache")
        return None

def deploy_contract():
    """Deploy the SecureShare smart contract"""
    w3 = get_web3()
    if not w3:
        return None

    # Read the Solidity contract
    contract_path = 'blockchain/contracts/SecureShare.sol'
    with open(contract_path, 'r') as file:
        contract_source = file.read()

    # Compile the contract
    compiled_sol = compile_source(
        contract_source,
        output_values=['abi', 'bin'],
        solc_version='0.8.20'
    )
    
    contract_id, contract_interface = compiled_sol.popitem()
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']

    # Deploy the contract
    SecureShare = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Use the first account from Ganache
    account = w3.eth.accounts[0]
    
    # Build and send the deployment transaction
    tx = SecureShare.constructor().build_transaction({
        'from': account,
        'nonce': w3.eth.get_transaction_count(account),
        'gas': 3000000,
    })
    
    # For local Ganache, we can sign with default (no private key needed for first account usually)
    tx_hash = w3.eth.send_transaction(tx)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    contract_address = tx_receipt.contractAddress
    print(f"✅ SecureShare Contract deployed at address: {contract_address}")
    
    # Save contract info for later use
    contract_data = {
        'address': contract_address,
        'abi': abi
    }
    
    with open('blockchain/contract_info.json', 'w') as f:
        json.dump(contract_data, f, indent=4)
    
    return contract_address, abi

# Test functions
if __name__ == "__main__":
    print("Testing connection and deployment...")
    deploy_contract()