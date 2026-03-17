import socket
import ssl
import threading

HOST = "0.0.0.0"
PORT_PLAIN = 5000
PORT_TLS = 5001

clients = {}   # nick -> socket


def broadcast_users():
    users = ",".join(clients.keys())
    msg = f"USERS:{users}"

    print(f"[USERS LIST] {users}")

    for c in clients.values():
        try:
            c.send(msg.encode())
        except:
            pass


def handle_client(conn, addr):

    try:
        data = conn.recv(1024)

        if not data:
            conn.close()
            return

        msg = data.decode()

        if not msg.startswith("NICK:"):
            conn.close()
            return

        nick = msg.split(":", 1)[1]

    except:
        conn.close()
        return

    clients[nick] = conn

    print(f"[JOIN] {nick} from {addr}")
    print(f"[CLIENT COUNT] {len(clients)}")

    broadcast_users()

    while True:
        try:
            data = conn.recv(1024)

            if not data:
                print(f"[NO DATA] {nick}")
                break

            msg = data.decode()

            print(f"[RAW MESSAGE] {nick}: {msg}")

            # wiadomość prywatna
            if msg.startswith("PM:"):
                try:
                    _, target, text = msg.split(":", 2)

                    if target in clients:
                        # wysyłamy strukturalnie
                        clients[target].send(f"PM:{nick}:{target}:{text}".encode())
                        print(f"[PM] {nick} -> {target}: {text}")
                    else:
                        conn.send(f"SERVER:user {target} not found".encode())

                except Exception as e:
                    print(f"[PM ERROR] {e}")

            # wiadomość publiczna
            elif msg.startswith("MSG:"):
                text = msg.split(":", 1)[1]

                for user, client in clients.items():
                    if client != conn:
                        client.send(f"MSG:{nick}:{text}".encode())

            else:
                print("[UNKNOWN FORMAT]", msg)

        except Exception as e:
            print(f"[ERROR] {nick} -> {e}")
            break

    print(f"[DISCONNECTED] {nick}")

    if nick in clients:
        del clients[nick]

    broadcast_users()

    conn.close()


def accept_plain(sock):
    while True:
        conn, addr = sock.accept()
        print(f"[PLAIN CONNECT] {addr}")

        threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        ).start()


def accept_tls(sock, context):
    while True:
        conn, addr = sock.accept()

        try:
            tls_conn = context.wrap_socket(conn, server_side=True)
        except Exception as e:
            print("[TLS ERROR]", e)
            continue

        print(f"[TLS CONNECT] {addr}")

        threading.Thread(
            target=handle_client,
            args=(tls_conn, addr),
            daemon=True
        ).start()


plain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
plain_sock.bind((HOST, PORT_PLAIN))
plain_sock.listen()

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