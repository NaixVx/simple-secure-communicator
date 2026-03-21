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

```bash
mkdir -p certs

openssl req -x509 -newkey rsa:4096 \
-keyout certs/key.pem \
-out certs/cert.pem \
-days 365 \
-nodes \
-subj "/CN=localhost" \
-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
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
