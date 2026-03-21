# Chat App (Socket + TLS)

A simple chat application (public + private messages) written in Python.

###  Created to showcase how TLS works.

## Features
- global chat
- private messages (PM)
- user list
- optional TLS (SSL)
- GUI (customtkinter)

---

## Requirements
- Python 3.10+
- openssl
- Linux / WSL (tested)

---

## 🔐 Generating TLS certificates

In the project directory:

### - Default version:

```bash
mkdir -p certs
cd certs

# 1. Create local CA (trusted by clients)
openssl genrsa -out ca.key 2048

openssl req -x509 -new -nodes \
-key ca.key \
-sha256 -days 3650 \
-out ca.pem \
-subj "/CN=LocalCA"

# 2. Create server key + CSR (use server IP)
openssl req -newkey rsa:2048 -nodes \
-keyout server.key \
-out server.csr \
-subj "/CN=192.168.1.4"

# 3. Sign server certificate with CA
openssl x509 -req \
-in server.csr \
-CA ca.pem \
-CAkey ca.key \
-CAcreateserial \
-out server.pem \
-days 365 \
-sha256 \
-extfile <(printf "subjectAltName=IP:192.168.1.4")
```
## 📦 Distribution

###  Copy `ca.pem` to all client machines

### - Localhost version:
```bash
mkdir -p certs
cd certs

# CA
openssl genrsa -out ca.key 2048

openssl req -x509 -new -nodes \
-key ca.key \
-sha256 -days 3650 \
-out ca.pem \
-subj "/CN=LocalCA"

# Server cert for localhost
openssl req -newkey rsa:2048 -nodes \
-keyout server.key \
-out server.csr \
-subj "/CN=localhost"

openssl x509 -req \
-in server.csr \
-CA ca.pem \
-CAkey ca.key \
-CAcreateserial \
-out server.pem \
-days 365 \
-sha256 \
-extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1")
```

## ▶️ Running the server
```bash
python3 server.py
```
The server starts on:
- 5000 → plain TCP
- 5001 → TLS

## ▶️ Running the client (venv)
```bash
./run.sh
```
or
```bash
python client.py  # inside virtual environment
```
