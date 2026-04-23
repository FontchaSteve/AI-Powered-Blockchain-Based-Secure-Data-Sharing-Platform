"""
Run this script whenever Ganache restarts to redeploy the SecureShare contract.
Usage: python redeploy_contract.py
"""
import json, os, re, sys

BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
SOL_PATH           = os.path.join(BASE_DIR, "blockchain", "contracts", "SecureShare.sol")
CONTRACT_INFO_PATH = os.path.join(BASE_DIR, "blockchain", "contract_info.json")
CONTRACT_PY_PATH   = os.path.join(BASE_DIR, "blockchain", "contract_interaction.py")
GANACHE_URL        = "http://127.0.0.1:7545"

def deploy():
    print("=" * 60)
    print("  SecureShare Contract Redeployment")
    print("=" * 60)

    from web3 import Web3
    from solcx import compile_source, install_solc

    print(f"\n[1/5] Connecting to Ganache at {GANACHE_URL} ...")
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        print("Cannot connect to Ganache. Make sure Ganache is open first.")
        sys.exit(1)
    print(f"Connected — {len(w3.eth.accounts)} accounts available")
    account = w3.eth.accounts[0]
    print(f"Deploying from: {account}")

    print("\n[2/5] Installing Solidity compiler ...")
    try:
        install_solc("0.8.19")
    except Exception as e:
        print(f"Already installed: {e}")

    print("[3/5] Compiling SecureShare.sol ...")
    with open(SOL_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    compiled = compile_source(source, output_values=["abi", "bin"], solc_version="0.8.19")
    _, interface = compiled.popitem()
    abi      = interface["abi"]
    bytecode = interface["bin"]
    print("Compiled successfully")

    print("[4/5] Deploying contract ...")
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor().build_transaction({
        "from": account,
        "nonce": w3.eth.get_transaction_count(account),
        "gas": 3000000,
    })
    tx_hash = w3.eth.send_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    new_addr = receipt.contractAddress
    print(f"Contract deployed at: {new_addr}")

    print("[5/5] Updating config files ...")
    with open(CONTRACT_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump({"address": new_addr, "abi": abi}, f, indent=4)
    print("contract_info.json updated")

    with open(CONTRACT_PY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'CONTRACT_ADDRESS\s*=\s*"0x[0-9a-fA-F]+"',
        f'CONTRACT_ADDRESS = "{new_addr}"',
        content,
    )
    with open(CONTRACT_PY_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("contract_interaction.py updated")

    print("\n" + "=" * 60)
    print(f"  ALL DONE! New address: {new_addr}")
    print("  Now run: python manage.py runserver")
    print("=" * 60)

if __name__ == "__main__":
    deploy()