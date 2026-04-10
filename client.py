import socket
import ssl
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import simpledialog, messagebox
import hashlib


HOST = None  # set before running or via prompt

PORT_PLAIN = None
PORT_TLS = None
EXPECTED_CERT_FP = None

sock = None
nickname = None
current_chat = "GLOBAL"

chat_history = {
    "GLOBAL": []
}


# ------------------ LOGGING ------------------

def log(msg):
    print("[CLIENT]", msg)

# ------------------ FINGERPRINT ------------------

def load_fingerprint():
    try:
        with open("certs/fingerprint.txt", "r") as f:
            fp = f.read().strip().replace(":", "")

        if len(fp) != 64:
            raise ValueError("Invalid fingerprint length")

        return bytes.fromhex(fp)

    except Exception as e:
        log(f"Fingerprint load error: {e}")
        return None

# ------------------ UI HELPERS ------------------

def safe_insert(msg):
    root.after(0, lambda: (chat.insert("end", msg + "\n"), chat.see("end")))


def refresh_chat_view():
    chat.delete("1.0", "end")

    chat_history.setdefault(current_chat, [])

    for msg in chat_history[current_chat]:
        chat.insert("end", msg + "\n")

    chat.see("end")


def update_user_list(users):
    user_list.delete(0, tk.END)
    user_list.insert(tk.END, "GLOBAL")

    for u in users:
        if u != nickname:
            user_list.insert(tk.END, u)


# ------------------ NETWORK ------------------

def create_socket(use_tls, host, port_plain, port_tls):
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if use_tls:
        context = ssl.create_default_context(cafile="certs/ca.pem")
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        wrapped = context.wrap_socket(raw_sock, server_hostname=host)
        return wrapped, port_tls
    else:
        return raw_sock, port_plain


def connect_to_server():
    global sock

    if not HOST:
        log("ERROR: Configure server IP")
        return

    # close old socket safely
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    use_tls = tls_var.get()

    try:
        new_sock, port = create_socket(use_tls, HOST, PORT_PLAIN, PORT_TLS)
        new_sock.connect((HOST, port))

        # ---- CERTIFICATE PINNING ----
        if use_tls:
            if EXPECTED_CERT_FP is None:
                log("No fingerprint loaded")
                return
            try:
                cert_bin = new_sock.getpeercert(binary_form=True)
                actual_fp = hashlib.sha256(cert_bin).digest()
                log(f"Server fingerprint: {actual_fp.hex().upper()}")

                if actual_fp != EXPECTED_CERT_FP:
                    log("Certificate pinning FAILED")
                    log(f"Expected: {EXPECTED_CERT_FP.hex().upper()}")
                    log(f"Actual:   {actual_fp.hex().upper()}")

                    new_sock.close()
                    return

                log("Certificate pinning OK (fingerprint match)")

                # optional debug
                log(f"TLS version: {new_sock.version()}")
                log(f"Cipher: {new_sock.cipher()[0]}")

            except Exception as e:
                new_sock.close()
                log(f"Pinning error: {e}")
                return
        # --------------------------------

        new_sock.send(f"NICK:{nickname}".encode())

        sock = new_sock

        connection_label.configure(
            text=f"{HOST}:{port} | TLS={'ON' if use_tls else 'OFF'}"
        )

        threading.Thread(
            target=run_receive_loop,
            args=(new_sock,),
            daemon=True
        ).start()

        log("Connected")

    except Exception as e:
        log(f"Connection error: {e}")
        return

    refresh_chat_view()


def run_receive_loop(local_sock):
    while True:
        try:
            data = local_sock.recv(1024)

            if not data:
                log("Disconnected from server")
                break

            process_server_message(data.decode())

        except Exception as e:
            if local_sock is sock:
                log(f"Receive error: {e}")
                log("Connection lost")


# ------------------ MESSAGE PROCESSING ------------------

def process_server_message(msg):
    if msg.startswith("USERS:"):
        handle_users_message(msg)

    elif msg.startswith("PM:"):
        handle_private_message(msg)

    elif msg.startswith("MSG:"):
        handle_global_message(msg)

    else:
        log(f"Unknown message: {msg}")


def handle_users_message(msg):
    users = msg.split(":")[1].split(",")
    root.after(0, lambda: update_user_list(users))


def handle_private_message(msg):
    try:
        _, sender, receiver, text = msg.split(":", 3)

        chat_history.setdefault(sender, []).append(f"[PM from {sender}] {text}")

        if current_chat == sender:
            safe_insert(f"[PM from {sender}] {text}")

    except Exception as e:
        log(f"PM parse error: {e}")


def handle_global_message(msg):
    try:
        _, sender, text = msg.split(":", 2)

        chat_history.setdefault("GLOBAL", []).append(f"[{sender}]: {text}")

        if current_chat == "GLOBAL":
            safe_insert(f"[{sender}]: {text}")

    except Exception as e:
        log(f"MSG parse error: {e}")


# ------------------ USER ACTIONS ------------------

def send_message(event=None):
    global sock

    msg = entry.get()
    if not msg:
        return

    if not sock:
        log("Not connected")
        return

    try:
        if current_chat == "GLOBAL":
            sock.send(f"MSG:{msg}".encode())
            chat_history["GLOBAL"].append(f"Me: {msg}")
        else:
            sock.send(f"PM:{current_chat}:{msg}".encode())
            chat_history.setdefault(current_chat, []).append(
                f"[PM to {current_chat}] {msg}"
            )

        refresh_chat_view()

    except Exception as e:
        log(f"Send error: {e}")
        sock = None

    entry.delete(0, "end")


def select_chat(event):
    global current_chat

    selection = user_list.curselection()
    if not selection:
        return

    current_chat = user_list.get(selection[0])
    chat_label.configure(text=f"Chat: {current_chat}")
    refresh_chat_view()


def toggle_tls():
    if HOST:
        connect_to_server()


# ------------------ GUI SETUP ------------------

def prompt_connection_config(root):
    dialog = tk.Toplevel(root)
    dialog.title("Connect to Server")
    dialog.geometry("300x200")
    dialog.grab_set()

    tk.Label(dialog, text="Server IP:").pack()
    ip_entry = tk.Entry(dialog)
    ip_entry.insert(0, "127.0.0.1")
    ip_entry.pack()

    tk.Label(dialog, text="Plain Port:").pack()
    plain_entry = tk.Entry(dialog)
    plain_entry.insert(0, "49152")
    plain_entry.pack()

    tk.Label(dialog, text="TLS Port:").pack()
    tls_entry = tk.Entry(dialog)
    tls_entry.insert(0, "49153")
    tls_entry.pack()

    result = None

    def confirm():
        nonlocal result
        try:
            host = ip_entry.get().strip()
            plain = int(plain_entry.get())
            tls = int(tls_entry.get())

            if not host:
                raise ValueError("Host is empty")

            if not (1 <= plain <= 65535 and 1 <= tls <= 65535):
                raise ValueError("Ports must be 1–65535")

            if plain == tls:
                raise ValueError("Ports must be different")

            result = {
                "host": host,
                "plain": plain,
                "tls": tls
            }

            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(dialog, text="Connect", command=confirm).pack(pady=10)

    root.wait_window(dialog)
    return result


def setup_gui():
    global root, chat, entry, user_list, chat_label, tls_var

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Chat")
    root.geometry("700x450")

    # nickname
    global nickname
    nickname = simpledialog.askstring("Nickname", "Enter nickname:", parent=root) or "Anonymous"

    # --- TOP BAR ---
    top_bar = ctk.CTkFrame(root)
    top_bar.pack(fill="x")

    logged_label = ctk.CTkLabel(top_bar, text=f"Logged as: {nickname}")
    logged_label.pack(side="left", padx=10, pady=5)

    tls_var = tk.BooleanVar()

    tls_check = ctk.CTkCheckBox(
        top_bar,
        text="TLS",
        variable=tls_var,
        command=toggle_tls,
        width=60
    )
    tls_check.pack(side="right", padx=10)

    # --- MAIN ---
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # sidebar
    user_list = tk.Listbox(main_frame, width=20)
    user_list.bind("<<ListboxSelect>>", select_chat)
    user_list.insert(tk.END, "GLOBAL")
    user_list.pack(side="left", fill="y", padx=(0, 10))

    # chat area
    chat_frame = ctk.CTkFrame(main_frame)
    chat_frame.pack(side="right", fill="both", expand=True)

    global connection_label
    connection_label = ctk.CTkLabel(chat_frame, text="Not connected")
    connection_label.pack(anchor="w", padx=10)

    chat_label = ctk.CTkLabel(chat_frame, text=f"Chat: {current_chat}")
    chat_label.pack(anchor="w", padx=10, pady=(5, 0))

    chat = ctk.CTkTextbox(chat_frame)
    chat.pack(fill="both", expand=True, padx=10, pady=5)

    # input
    bottom_bar = ctk.CTkFrame(chat_frame)
    bottom_bar.pack(fill="x", padx=10, pady=5)

    entry = ctk.CTkEntry(bottom_bar)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    entry.bind("<Return>", send_message)

    send_btn = ctk.CTkButton(bottom_bar, text="Send", width=80, command=send_message)
    send_btn.pack(side="right")

    def on_close():
        global sock

        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                sock.close()
            except:
                pass

        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    return root


# ------------------ MAIN ------------------

def main():
    global HOST, PORT_PLAIN, PORT_TLS, EXPECTED_CERT_FP
    
    root = setup_gui()

    config = prompt_connection_config(root)
    if not config:
        return

    HOST = config["host"]
    PORT_PLAIN = config["plain"]
    PORT_TLS = config["tls"]

    EXPECTED_CERT_FP = load_fingerprint()

    if EXPECTED_CERT_FP is None:
        log("Cannot start without valid fingerprint")
        return

    log(f"Pinned fingerprint: {EXPECTED_CERT_FP.hex().upper()}")

    connect_to_server()
    root.mainloop()


if __name__ == "__main__":
    main()