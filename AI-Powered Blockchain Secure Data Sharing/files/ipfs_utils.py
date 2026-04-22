"""
IPFS utilities using Pinata as the pinning service.

Pinata keeps your encrypted files online permanently — even when your
machine is off.  Files are retrieved by their CID from any IPFS gateway.

Setup (one-time):
  1. Go to https://app.pinata.cloud  →  create a free account
  2. Go to API Keys  →  create a new key with pinFileToIPFS + unpin permissions
  3. Add to your .env file:
       PINATA_API_KEY=your_api_key_here
       PINATA_API_SECRET=your_api_secret_here
"""

import os
import io
import requests
from django.conf import settings

# ── Pinata endpoints ──────────────────────────────────────────────────────────
PINATA_PIN_URL    = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_UNPIN_URL  = "https://api.pinata.cloud/pinning/unpin/{cid}"
PINATA_GATEWAY    = "https://gateway.pinata.cloud/ipfs/{cid}"
PUBLIC_GATEWAY    = "https://cloudflare-ipfs.com/ipfs/{cid}"   # fallback


def _get_headers():
    """Return auth headers using env variables."""
    api_key    = os.getenv("PINATA_API_KEY", "")
    api_secret = os.getenv("PINATA_API_SECRET", "")

    if not api_key or not api_secret:
        raise ValueError(
            "PINATA_API_KEY and PINATA_API_SECRET must be set in your .env file.\n"
            "Get them free at https://app.pinata.cloud"
        )
    return {
        "pinata_api_key":        api_key,
        "pinata_secret_api_key": api_secret,
    }


def upload_to_ipfs(encrypted_data: bytes, filename: str) -> str:
    """
    Upload encrypted file bytes to Pinata IPFS.

    Returns the CID (Content Identifier) string, e.g. 'QmXk9f2abc...'
    Raises an exception if the upload fails.
    """
    headers = _get_headers()

    # Wrap bytes in a file-like object so requests can stream it
    file_obj = io.BytesIO(encrypted_data)

    response = requests.post(
        PINATA_PIN_URL,
        files={"file": (filename, file_obj, "application/octet-stream")},
        headers=headers,
        timeout=120,   # 2 min — large files need time
    )

    if response.status_code != 200:
        raise ConnectionError(
            f"Pinata upload failed [{response.status_code}]: {response.text}"
        )

    data = response.json()
    cid  = data.get("IpfsHash")
    if not cid:
        raise ValueError(f"Pinata returned no CID. Response: {data}")

    return cid


def download_from_ipfs(cid: str) -> bytes:
    """
    Download encrypted file bytes from IPFS by CID.

    Tries Pinata's dedicated gateway first, then falls back to Cloudflare's
    public IPFS gateway if Pinata is slow or unavailable.
    """
    gateways = [
        PINATA_GATEWAY.format(cid=cid),
        PUBLIC_GATEWAY.format(cid=cid),
    ]

    last_error = None
    for url in gateways:
        try:
            response = requests.get(url, timeout=120, stream=True)
            if response.status_code == 200:
                return response.content
            last_error = f"HTTP {response.status_code} from {url}"
        except requests.RequestException as e:
            last_error = str(e)
            continue

    raise ConnectionError(
        f"Could not retrieve file from IPFS (CID: {cid}). "
        f"Last error: {last_error}"
    )


def unpin_from_ipfs(cid: str) -> bool:
    """
    Unpin (delete) a file from Pinata when a file is deleted from SecureShare.
    Returns True on success, False if the CID wasn't found (already gone).
    """
    try:
        headers  = _get_headers()
        response = requests.delete(
            PINATA_UNPIN_URL.format(cid=cid),
            headers=headers,
            timeout=30,
        )
        return response.status_code in (200, 404)
    except Exception:
        return False


def is_pinata_configured() -> bool:
    """Check if Pinata credentials are present in environment."""
    return bool(
        os.getenv("PINATA_API_KEY") and os.getenv("PINATA_API_SECRET")
    )


def get_ipfs_url(cid: str) -> str:
    """Return a public gateway URL for a given CID (for display purposes)."""
    return PINATA_GATEWAY.format(cid=cid)