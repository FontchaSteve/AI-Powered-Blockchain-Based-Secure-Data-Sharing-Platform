from web3 import Web3
from dotenv import load_dotenv
import os
import json

load_dotenv()

BASE_DIR           = os.path.dirname(os.path.abspath(__file__))
CONTRACT_INFO_PATH = os.path.join(BASE_DIR, 'contract_info.json')
CONTRACT_ADDRESS   = "0x0abdcBe80E8c54c8B1760f1A2C2482b5670afd9e"


def get_web3():
    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    return Web3(Web3.HTTPProvider(ganache_url))


def get_contract():
    w3 = get_web3()
    if not w3.is_connected():
        raise ConnectionError(
            "Cannot connect to Ganache. Make sure Ganache is open."
        )
    with open(CONTRACT_INFO_PATH, 'r', encoding='utf-8') as f:
        contract_data = json.load(f)
    address = contract_data.get('address', CONTRACT_ADDRESS)
    code = w3.eth.get_code(address)
    if code in (b'', b'\x00', '0x', '0x0'):
        raise RuntimeError(
            "Contract not found on blockchain. "
            "Run: python redeploy_contract.py"
        )
    contract = w3.eth.contract(address=address, abi=contract_data['abi'])
    return w3, contract


def is_blockchain_available():
    try:
        get_contract()
        return True, None
    except ConnectionError as e:
        return False, f"Ganache offline: {e}"
    except RuntimeError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)