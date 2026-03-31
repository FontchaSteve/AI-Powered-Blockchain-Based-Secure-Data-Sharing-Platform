# 🔐 AI-Powered Blockchain-Based Secure Data Sharing Platform

## 📌 Overview

This project is a secure web-based data sharing platform that integrates **Blockchain, Artificial Intelligence, and Cryptography** to provide a safe and tamper-proof environment for managing and sharing sensitive data.

The system ensures that all uploaded files are encrypted, access permissions are securely managed, and all activities are transparently logged using blockchain technology.
## cd "AI-Powered Blockchain Secure Data Sharing"
---

## 🚀 Features

* 🔐 Secure user authentication system
* 📁 Encrypted file upload and storage
* 🔗 Blockchain-based access control using smart contracts
* 📜 Immutable access logs stored on blockchain
* 👥 Role-based file sharing (owner & authorized users)
* 🤖 AI-based anomaly detection for suspicious behavior
* 📊 Activity monitoring and logging
* 🛡 Data integrity verification using file hashing

---

## 🏗 System Architecture

Frontend (HTML, CSS, Bootstrap)
⬇
Backend (Django - Python)
⬇
Database (SQLite)
⬇
Blockchain (Ganache + Solidity Smart Contract)

---

## 🧩 Technologies Used

### Backend

* Python (Django)

### Frontend

* HTML, CSS, Bootstrap

### Database

* SQLite

### Blockchain

* Ganache (Local Ethereum Network)
* Solidity (Smart Contracts)
* Web3.py (Blockchain Integration)

### Security

* AES Encryption (Python Cryptography Library)
* SHA-256 Hashing

### Artificial Intelligence

* Scikit-learn (Isolation Forest for anomaly detection)

---

## 🔐 How It Works

1. User uploads a file
2. File is encrypted using AES
3. Encrypted file is stored locally in the server
4. File hash is generated (SHA-256)
5. Hash and metadata are stored on blockchain
6. Owner can grant or revoke access using smart contract
7. When a user requests a file:

   * Blockchain verifies access permission
   * File is decrypted and served
   * Access event is logged on blockchain
8. AI module analyzes user behavior to detect anomalies

---

## 📂 Project Structure

secure_data_share/                  # Root project folder
├── manage.py
├── db.sqlite3                      # SQLite database (auto-created)
├── requirements.txt                # List all dependencies
├── .env                            # For local secrets (e.g., Ganache URL)
├── README.md

├── secure_data_share/              # Main Django project folder
│   ├── __init__.py
│   ├── settings.py                 # Add your apps, blockchain config, AI settings
│   ├── urls.py
│   ├── asgi.py / wsgi.py
│   └── celery.py                   # (Optional later for background AI tasks)

├── users/                          # Authentication & user management
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py                   # User model (extends AbstractUser)
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/users/            # login, register, profile

├── files/                          # File upload, encryption, access control
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                   # File & Access models
│   ├── views.py                    # upload, download, share views
│   ├── forms.py
│   ├── utils.py                    # encryption/decryption helpers (AES + Fernet)
│   ├── urls.py
│   └── templates/files/

├── blockchain/                     # Interaction with Ganache + Smart Contracts
│   ├── __init__.py
│   ├── contracts/                  # Solidity files
│   │   └── SecureShare.sol         # Smart contract for access control, hashes, logs
│   ├── web3_utils.py               # Web3.py helpers to interact with Ganache
│   ├── views.py                    # Views that call smart contract functions
│   └── tasks.py                    # (Optional) background tasks for on-chain logging

├── ai_monitor/                     # Local AI for anomaly detection & monitoring
│   ├── __init__.py
│   ├── models.py                   # (Optional) if you store AI results
│   ├── anomaly_detector.py         # Main AI logic (IsolationForest + rules)
│   ├── log_analyzer.py             # Process activity logs from DB
│   ├── views.py                    # Dashboard to view anomalies/alerts
│   ├── utils.py                    # Feature extraction from logs
│   └── templates/ai_monitor/       # anomaly dashboard, alerts

├── templates/                      # Global HTML templates (base.html, etc.)
│   └── base.html

├── static/                         # CSS, JS, images
│   ├── css/
│   └── js/

└── media/                          # Uploaded encrypted files (local storage)
    └── files/                      # Subfolder for actual file storage
---

## ⚙️ Installation Guide

### 1. Clone Repository

```bash
git clone https://github.com/your-username/secure-share.git
cd secure-share
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Django Server

```bash
python manage.py migrate
python manage.py runserver
```

---

## 🔗 Blockchain Setup

### 1. Install Ganache and start local blockchain

### 2. Deploy Smart Contract

```bash
truffle compile
truffle migrate
```

### 3. Update contract address and ABI in Django project

---

## 🤖 AI Module

The system uses **Isolation Forest** for anomaly detection based on:

* Login frequency
* File access behavior
* Failed attempts

Suspicious users are flagged for monitoring.

---

## 🔒 Security Features

* AES file encryption
* Secure password hashing
* Blockchain-based access control
* Tamper-proof logging
* AI-driven threat detection

---

## 🎯 Use Cases

* Secure document sharing
* Enterprise data protection
* Academic record management
* Confidential file storage

---

## 📌 Future Improvements

* Cloud deployment
* Real Ethereum/Testnet integration
* Advanced AI models
* Mobile application support

---

## 👨‍💻 Author

Final Year Cybersecurity Project
