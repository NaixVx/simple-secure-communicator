import socket
import ssl
import threading
import logging
import tkinter as tk
from tkinter import messagebox


clients = {}
clients_lock = threading.Lock()

# ------------------ LOGGING ------------------

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(threadName)s | %(message)s"
    ))
    logger.addHandler(handler)


# ------------------ PORT AND IP CHECK ------------------

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ------------------ LOGGING TO GUI ------------------

class TextHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.widget.insert(tk.END, msg + "\n")
            self.widget.see(tk.END)

        self.widget.after(0, append)


# ------------------ GUI ------------------

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Control")

        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        # --- MODE SELECTION ---
        self.bind_mode = tk.StringVar(value="local")

        tk.Label(frame, text="Mode:").grid(row=0, column=0)

        tk.Radiobutton(frame, text="Local (127.0.0.1)",
                       variable=self.bind_mode, value="local").grid(row=0, column=1, sticky="w")

        tk.Radiobutton(frame, text="Network (LAN)",
                       variable=self.bind_mode, value="network").grid(row=0, column=2, sticky="w")

        # --- PORTS ---
        tk.Label(frame, text="Plain Port:").grid(row=1, column=0)
        self.plain_entry = tk.Entry(frame)
        self.plain_entry.insert(0, "5000")
        self.plain_entry.grid(row=1, column=1)

        tk.Label(frame, text="TLS Port:").grid(row=2, column=0)
        self.tls_entry = tk.Entry(frame)
        self.tls_entry.insert(0, "5001")
        self.tls_entry.grid(row=2, column=1)

        self.start_btn = tk.Button(frame, text="Start Server", command=self.start_server)
        self.start_btn.grid(row=3, columnspan=3, pady=5)

        # --- CONNECTION INFO ---
        self.info_label = tk.Label(root, text="Not running")
        self.info_label.pack()

        # --- LOGS ---
        self.log_text = tk.Text(root, height=20, width=80)
        self.log_text.pack(padx=10, pady=10)

        logger.handlers.clear()

        gui_handler = TextHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        ))

        logger.addHandler(gui_handler)

    def start_server(self):
        try:
            plain_port = int(self.plain_entry.get())
            tls_port = int(self.tls_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ports must be integers")
            return

        if not (1 <= plain_port <= 65535 and 1 <= tls_port <= 65535):
            messagebox.showerror("Error", "Ports must be between 1 and 65535")
            return

        if plain_port == tls_port:
            messagebox.showerror("Error", "Ports must be different")
            return

        if not is_port_free(plain_port) or not is_port_free(tls_port):
            messagebox.showerror("Error", "One of the ports is already in use")
            return

        # --- determine bind host ---
        if self.bind_mode.get() == "local":
            host = "127.0.0.1"
            display_ip = "127.0.0.1"
        else:
            host = "0.0.0.0"
            display_ip = get_local_ip()

        logger.info("STARTING mode=%s host=%s", self.bind_mode.get(), host)

        # update UI with connection info
        self.info_label.config(
            text=f"Connect: {display_ip}:{plain_port} (plain) | {display_ip}:{tls_port} (TLS)"
        )

        threading.Thread(
            target=self.run_server,
            args=(host, plain_port, tls_port),
            daemon=True
        ).start()

        self.start_btn.config(state="disabled")

    def run_server(self, host, plain_port, tls_port):
        plain = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        plain.bind((host, plain_port))
        plain.listen()

        tls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tls.bind((host, tls_port))
        tls.listen()

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain("certs/server.pem", "certs/server.key")

        logger.info("SERVER_RUNNING host=%s plain=%d tls=%d", host, plain_port, tls_port)

        start_acceptors(plain, tls, context)

        threading.Event().wait()


# ------------------ CLIENT MANAGEMENT ------------------

def broadcast_users():
    with clients_lock:
        users = ",".join(clients.keys())
        targets = list(clients.values())

    logger.info("USERS_LIST users=%s", users)

    for c in targets:
        try:
            c.send(f"USERS:{users}".encode())
        except Exception:
            logger.warning("SEND_FAILED USERS_LIST")


def register_client(nick, conn, addr):
    with clients_lock:
        clients[nick] = conn

    logger.info("JOIN nick=%s addr=%s", nick, addr)
    broadcast_users()


def unregister_client(nick):
    with clients_lock:
        clients.pop(nick, None)

    logger.info("DISCONNECT nick=%s", nick)
    broadcast_users()


# ------------------ MESSAGE HANDLING ------------------

def process_client_message(conn, nick, msg):
    if msg.startswith("PM:"):
        process_private_message(conn, nick, msg)
    elif msg.startswith("MSG:"):
        process_broadcast_message(conn, nick, msg)
    else:
        logger.warning("UNKNOWN_FORMAT nick=%s msg=%s", nick, msg)


def process_private_message(conn, nick, msg):
    try:
        _, target, text = msg.split(":", 2)

        with clients_lock:
            target_conn = clients.get(target)

        if target_conn:
            target_conn.send(f"PM:{nick}:{target}:{text}".encode())
            logger.info("PM from=%s to=%s", nick, target)
        else:
            conn.send(f"SERVER:user {target} not found".encode())

    except Exception:
        logger.exception("PM_ERROR nick=%s", nick)


def process_broadcast_message(conn, nick, msg):
    text = msg.split(":", 1)[1]

    with clients_lock:
        targets = [c for c in clients.values() if c != conn]

    for c in targets:
        try:
            c.send(f"MSG:{nick}:{text}".encode())
        except Exception:
            logger.warning("BROADCAST_FAILED from=%s", nick)


# ------------------ CLIENT SESSION ------------------

def receive_client_nick(conn):
    try:
        data = conn.recv(1024)
        if not data:
            return None

        msg = data.decode()
        if not msg.startswith("NICK:"):
            return None

        return msg.split(":", 1)[1]

    except Exception:
        return None


def run_client_session(conn, addr):
    nick = receive_client_nick(conn)

    if not nick:
        conn.close()
        return

    register_client(nick, conn, addr)

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            process_client_message(conn, nick, data.decode())

        except Exception:
            logger.exception("CLIENT_ERROR nick=%s", nick)
            break

    unregister_client(nick)
    conn.close()


# ------------------ ACCEPT LOOPS ------------------

def run_plain_accept_loop(sock):
    while True:
        conn, addr = sock.accept()
        logger.info("PLAIN_CONNECT addr=%s", addr)

        threading.Thread(
            target=run_client_session,
            args=(conn, addr),
            daemon=True
        ).start()


def run_tls_accept_loop(sock, context):
    while True:
        conn, addr = sock.accept()

        try:
            conn = context.wrap_socket(conn, server_side=True)
        except Exception:
            logger.exception("TLS_ERROR addr=%s", addr)
            continue

        logger.info("TLS_CONNECT addr=%s", addr)

        threading.Thread(
            target=run_client_session,
            args=(conn, addr),
            daemon=True
        ).start()


def start_acceptors(plain, tls, context):
    threading.Thread(target=run_plain_accept_loop, args=(plain,), daemon=True).start()
    threading.Thread(target=run_tls_accept_loop, args=(tls, context), daemon=True).start()


# ------------------ MAIN ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()