import socket
import ssl
import threading

HOST = "0.0.0.0"
PORT_PLAIN = 5000
PORT_TLS = 5001

clients = []

def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            msg = data.decode()
            print(f"[MESSAGE] {addr}: {msg}")

            for c in clients:
                if c != conn:
                    c.send(f"{addr}: {msg}".encode())

        except:
            break

    print(f"[DISCONNECTED] {addr}")
    clients.remove(conn)
    conn.close()

def accept_plain(sock):
    while True:
        conn, addr = sock.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def accept_tls(sock, context):
    while True:
        conn, addr = sock.accept()
        tls_conn = context.wrap_socket(conn, server_side=True)
        clients.append(tls_conn)
        threading.Thread(target=handle_client, args=(tls_conn, addr), daemon=True).start()


# socket plaintext
plain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
plain_sock.bind((HOST, PORT_PLAIN))
plain_sock.listen()

# socket TLS
tls_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tls_sock.bind((HOST, PORT_TLS))
tls_sock.listen()

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="certs/cert.pem", keyfile="certs/key.pem")

print("Server running")
print("Plain port:", PORT_PLAIN)
print("TLS port:", PORT_TLS)

threading.Thread(target=accept_plain, args=(plain_sock,), daemon=True).start()
threading.Thread(target=accept_tls, args=(tls_sock, context), daemon=True).start()

while True:
    pass