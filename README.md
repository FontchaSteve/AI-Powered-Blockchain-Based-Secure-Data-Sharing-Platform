# 🔐 AI-Powered Blockchain-Based Secure Data Sharing Platform

## 📌 Overview

This project is a secure web-based data sharing platform that integrates **Blockchain, Artificial Intelligence, Cryptography, and IPFS** to provide a safe and tamper-proof environment for managing and sharing sensitive data.

The system ensures that all uploaded files are encrypted, stored securely online via IPFS, access permissions are managed on the blockchain using smart contracts, and all activities are transparently logged and monitored by an AI anomaly detection engine.

---

## 🔑 Admin Access

```
Admin Panel (Custom):  http://127.0.0.1:8000/accounts/manage/
Django Admin:          http://127.0.0.1:8000/admin/
Username:              WANDA
Password:              Wanda@2022
```

---

## 🚀 Features

### 🔐 Authentication & User Management
- Secure user registration, login and logout
- Auto-assignment of unique blockchain wallet per user on registration — no two users share the same Ganache account
- Password change and email update from profile page
- Failed login attempts are logged and monitored by AI

### 📁 File Management
- AES-256 encrypted file upload (max 50 MB)
- SHA-256 file hashing for integrity verification
- Search, filter and sort files by name, type, storage mode and blockchain status
- Download count tracking — see how many times each file has been downloaded
- File deletion removes from IPFS and local storage

### ☁ IPFS Storage (Pinata)
- Encrypted files are stored online on IPFS via Pinata — not on local disk
- Files remain accessible even if the server is offline
- Falls back to local storage automatically if IPFS is unavailable
- Each file gets a unique CID (Content Identifier) stored in the database

### ⛓ Blockchain Integration (Ganache + Solidity)
- File hash registered on blockchain at upload time
- Smart contract functions: `uploadFile`, `grantAccess`, `revokeAccess`, `hasAccess`
- Blockchain verification page — verify any file by filename or SHA-256 hash
- Each user has their own wallet address — blockchain records show the real owner
- `redeploy_contract.py` script to redeploy contract after Ganache restarts

### 👥 File Sharing
- Share any file with any registered user by username
- Set expiry dates: 1 day, 3 days, 7 days, 14 days, 1 month, 3 months, 6 months, 1 year, or permanent
- Access automatically expires at the set date — no manual intervention needed
- Revoke access at any time from the Share page
- Blockchain `grantAccess()` called when both users have wallets assigned
- Email notification sent to recipient when a file is shared with them

### 📧 Email Notifications
- Beautiful HTML email sent to recipient when a file is shared
- Email shows file name, file size, storage type, blockchain status
- Clearly shows expiry date and days remaining (or "permanent access")
- Configured via Gmail SMTP with App Password
- Falls back silently if email is not configured

### 🤖 AI Anomaly Detection
- Isolation Forest model analyses each user's own activity logs
- Detects suspicious upload, download, login and access patterns
- Each user only sees anomalies from their own account — fully isolated
- Activates after 10 or more activity events per user
- Activity log shows last 50 events per user with action, timestamp, IP, status

### 🛡 Custom Admin Panel
- Full system control at `/accounts/manage/` (superusers only)
- **Users tab** — search, filter by status and wallet, manage any user
- **Files tab** — view all files system-wide, filter by storage type, delete any file
- **Activity tab** — filter logs by action type and success/failure, export all logs as CSV
- Per-user management: ban/activate, grant/remove staff, reassign wallet, delete user
- Visible only to superusers — shown as orange "Admin" link in navbar

---

## 🏗 System Architecture

```
Browser (Cyberpunk Dark UI)
        ⬇
Backend (Django 5 — Python)
        ⬇
    ┌───────────────────────────────┐
    │  SQLite Database              │  Users, files, shares, activity logs
    │  IPFS / Pinata (Online)       │  Encrypted file storage
    │  Ganache (Local Blockchain)   │  File hashes, ownership, access control
    └───────────────────────────────┘
        ⬇
AI Monitor (Isolation Forest — Scikit-learn)
```

---

## 🧩 Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python, Django 5 |
| Frontend | HTML, CSS (custom cyberpunk dark theme), Bootstrap Icons |
| Database | SQLite |
| Blockchain | Ganache, Solidity, Web3.py |
| File Storage | IPFS via Pinata API |
| Encryption | AES-256 (PyCryptodome), SHA-256 |
| AI | Scikit-learn (Isolation Forest), Pandas, NumPy |
| Email | Django SMTP (Gmail) |

---

## 🔐 How It Works

### Upload Flow
1. User selects a file (max 50 MB)
2. File is hashed with SHA-256
3. File is encrypted with AES-256
4. Encrypted file uploaded to IPFS via Pinata → CID returned
5. SHA-256 hash registered on Ganache blockchain under user's wallet
6. File metadata (CID, hash, tx hash, size) saved to SQLite

### Download Flow
1. User clicks Download
2. Django fetches CID from database
3. Encrypted file retrieved from IPFS
4. File decrypted in memory with AES-256
5. Decrypted file sent to browser
6. Download count incremented by 1
7. Activity logged

### Share Flow
1. Owner enters recipient username and selects expiry
2. FileShare record created in database with expiry timestamp
3. Blockchain `grantAccess()` called if both users have wallets
4. Beautiful HTML email sent to recipient's inbox
5. Recipient sees file in "Shared With Me" page
6. At expiry time, download is automatically blocked

### AI Monitor Flow
1. Every upload, download, login, share is logged to ActivityLog
2. User opens AI Monitor page
3. Isolation Forest model runs on that user's last 30 days of logs
4. Anomalous events are flagged and shown as alerts
5. Only the current user's own logs are ever analysed

---

## 📂 Project Structure

```
AI-Powered Blockchain Secure Data Sharing/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── .env                          # Ganache URL, Pinata keys, Gmail credentials
├── redeploy_contract.py          # Run after Ganache restarts
├── README.md

├── ai_powered_blockchain_secure_data_sharing/
│   ├── settings.py               # All config including email and IPFS
│   └── urls.py

├── users/
│   ├── models.py                 # CustomUser with wallet_address, ActivityLog
│   ├── views.py                  # Auth + profile + full custom admin panel
│   ├── urls.py
│   ├── admin.py
│   └── templates/users/          # login.html, register.html, profile.html

├── files/
│   ├── models.py                 # File (with download_count, ipfs_cid), FileShare
│   ├── views.py                  # Upload, download, share, verify, delete
│   ├── email_utils.py            # HTML email notifications
│   ├── ipfs_utils.py             # Pinata IPFS upload/download/unpin
│   ├── encryption_utils.py       # AES-256 encrypt/decrypt, SHA-256 hash
│   ├── urls.py
│   └── templates/files/          # dashboard, my_files, upload, share_file,
│                                 # shared_with_me

├── blockchain/
│   ├── contract_interaction.py   # get_contract(), is_blockchain_available()
│   ├── contract_info.json        # Deployed contract address + ABI
│   └── contracts/
│       └── SecureShare.sol       # Solidity smart contract

├── ai_monitor/
│   ├── anomaly_detector.py       # Isolation Forest per-user analysis
│   ├── views.py                  # Per-user AI dashboard
│   └── templates/ai_monitor/     # dashboard.html

├── admin_panel/
│   └── templates/admin_panel/    # dashboard.html, user_detail.html

└── templates/
    ├── base.html                 # Global cyberpunk dark theme base
    └── emails/
        └── file_shared.html      # HTML email template for share notifications
```

---

## ⚙️ Installation Guide

### 1. Clone Repository
```bash
git clone https://github.com/your-username/secure-share.git
cd "AI-Powered Blockchain Secure Data Sharing"
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Edit `.env` in the project root:
```env
# Ganache
GANACHE_URL=http://127.0.0.1:7545
NETWORK_ID=5777

# Pinata IPFS (get free at https://app.pinata.cloud)
PINATA_API_KEY=your_pinata_api_key
PINATA_API_SECRET=your_pinata_api_secret

# Gmail SMTP (use Gmail App Password, NOT your normal password)
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Start Ganache
Open the Ganache desktop app and click your saved workspace.

### 8. Deploy Smart Contract (first time only)
```bash
python redeploy_contract.py
```

### 9. Start the Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## 🔄 Every Time You Run the Project

```
1. Open Ganache desktop app → click your workspace
2. python manage.py runserver
```

That is all. Only run `redeploy_contract.py` again if Ganache loses its state.

---

## 🔗 Blockchain Setup Details

The smart contract (`SecureShare.sol`) handles:
- `uploadFile(hash)` — register a file hash under the caller's wallet
- `grantAccess(hash, wallet, expiry)` — give another wallet access to a file
- `revokeAccess(hash, wallet)` — remove access
- `hasAccess(hash, wallet)` — check if a wallet has access
- `files(hash)` — get file metadata from chain

After deploying, `contract_info.json` is updated automatically with the new address and ABI.

---

## 🤖 AI Module Details

The Isolation Forest model is trained on each user's own activity logs from the last 30 days. Features used: action type, hour of day, day of week, success/failure status. Contamination is set to 15% meaning roughly 1 in 7 events will be flagged as anomalous if unusual. At least 10 events are required before the model activates.

---

## 📧 Email Setup (Gmail)

1. Go to `myaccount.google.com` → Security
2. Enable 2-Step Verification
3. Search "App passwords" → Create one named `SecureShare`
4. Copy the 16-character password into `.env` as `EMAIL_HOST_PASSWORD`
5. Restart the server

---

## 🔒 Security Features Summary

| Feature | Implementation |
|---|---|
| File encryption | AES-256 (PyCryptodome) |
| File integrity | SHA-256 hash on blockchain |
| Password hashing | Django PBKDF2 |
| Access control | Blockchain smart contract + Django DB |
| Activity logging | ActivityLog model — every action recorded |
| Anomaly detection | Isolation Forest (Scikit-learn) |
| Online storage | IPFS via Pinata — decentralized |
| Time-limited sharing | Expiry timestamps in database |
| Email notifications | Django SMTP — Gmail |

---

## 🎯 Use Cases

- Secure document sharing between colleagues
- Time-limited access to confidential reports
- Academic record and certificate management
- Enterprise data protection with full audit trail
- Blockchain-verified file ownership proof

---

## 📌 Future Improvements

- Cloud deployment (AWS / Heroku)
- Real Ethereum testnet integration (Sepolia)
- Mobile application support
- Two-factor authentication (2FA)
- File preview for images in browser
- Real-time notifications (WebSockets)
- Advanced AI models with more features

---

## 👨‍💻 Author

Final Year Cybersecurity Project