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

### Copy ca.pem to all client machines

The client must trust the same Certificate Authority as the server.
This requires copying certs/ca.pem from the server to every client device.

Example using scp:
```bash
scp certs/ca.pem user@client_ip:/path/to/project/certs/
```

### - Localhost version

```bash

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

### Certificate fingerprint (pinning)

In addition to standard certificate validation, the client uses certificate pinning to verify the identity of the server. This is done by comparing the SHA-256 fingerprint of the server certificate with a locally stored reference value.

After generating the server certificate, create the fingerprint:

```bash
openssl x509 -in certs/server.pem -noout -fingerprint -sha256 \
| cut -d'=' -f2 | tr -d '\n' > certs/fingerprint.txt
```

The resulting fingerprint.txt file must be copied to each client machine.

Example:
```bash
scp certs/fingerprint.txt user@client_ip:/path/to/project/certs/
```
The client will refuse the connection if the received server certificate fingerprint does not match the expected value.

### 👤 User management

Users are stored on the server side in a users.txt file.

```bash
./add_user.py
```
The script will:
- prompt for username and password
- hash the password using SHA-256
- append the user to users.txt
⚠️ Important:
- This must be executed on the server machine
- The client does not store or manage users
- Authentication is performed by the server during connection

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
