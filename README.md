# Chat App (Socket + TLS)

A simple chat application (public + private messages) written in Python.

### Created to showcase how TLS works

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

### - Default version

```bash
#!/usr/bin/env bash

mkdir -p certs
cd certs

IP="192.168.1.4" # use appropriate ip address

# CA
openssl genrsa -out ca.key 2048

openssl req -x509 -new -nodes \
-key ca.key \
-sha256 -days 3650 \
-out ca.pem \
-subj "/CN=LocalCA" \
-addext "basicConstraints=critical,CA:TRUE" \
-addext "keyUsage=critical,keyCertSign,cRLSign"

# Server CSR
openssl req -newkey rsa:2048 -nodes \
-keyout server.key \
-out server.csr \
-subj "/CN=$IP"

# Extensions
cat > server.ext <<EOF
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:$IP
EOF

# Sign
openssl x509 -req \
-in server.csr \
-CA ca.pem \
-CAkey ca.key \
-CAcreateserial \
-out server.pem \
-days 365 \
-sha256 \
-extfile server.ext
```

## 📦 Distribution

### Copy `ca.pem` to all client machines

### - Localhost version

```bash
#!/usr/bin/env bash

mkdir -p certs
cd certs

# CA
openssl genrsa -out ca.key 2048

openssl req -x509 -new -nodes \
-key ca.key \
-sha256 -days 3650 \
-out ca.pem \
-subj "/CN=LocalCA" \
-addext "basicConstraints=critical,CA:TRUE" \
-addext "keyUsage=critical,keyCertSign,cRLSign"

# Server key + CSR
openssl req -newkey rsa:2048 -nodes \
-keyout server.key \
-out server.csr \
-subj "/CN=localhost"

# Extensions
cat > server.ext <<EOF
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
EOF

# Sign cert
openssl x509 -req \
-in server.csr \
-CA ca.pem \
-CAkey ca.key \
-CAcreateserial \
-out server.pem \
-days 365 \
-sha256 \
-extfile server.ext
```

### Generate the fingerprint

```bash
openssl x509 -in certs/server.pem -noout -fingerprint -sha256 \
| cut -d'=' -f2 | tr -d '\n' > certs/fingerprint.txt
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
./run.sh # works on linux systems only 
```

or

```bash
python client.py  # inside virtual environment
```
