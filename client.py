import socket
import ssl
import threading
import tkinter as tk
from tkinter import simpledialog

HOST = "localhost"

sock = None
nickname = None

def log(msg):
    print("[CLIENT]", msg)

def connect():
    global sock

    if sock:
        try:
            log("Closing previous connection")
            sock.close()
        except:
            pass

    use_tls = tls_var.get()

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if use_tls:
        context = ssl.create_default_context(cafile="certs/cert.pem")
        sock = context.wrap_socket(raw_sock, server_hostname=HOST)
        port = 5001
    else:
        sock = raw_sock
        port = 5000

    try:
        log(f"Connecting to {HOST}:{port} TLS={use_tls}")
        sock.connect((HOST, port))

        # wysłanie nicka
        sock.send(f"NICK:{nickname}".encode())

        chat.insert(tk.END, f"Connected as {nickname} TLS={use_tls}\n")

        threading.Thread(target=receive, daemon=True).start()

    except Exception as e:
        log(f"Connection error: {e}")
        chat.insert(tk.END, f"Connection error: {e}\n")


def receive():
    global sock

    log("Receive thread started")

    while True:
        try:
            data = sock.recv(1024)

            if not data:
                log("Server closed connection")
                chat.insert(tk.END, "Disconnected from server\n")
                break

            msg = data.decode()

            log(f"Received: {msg}")

            # aktualizacja listy użytkowników
            if msg.startswith("USERS:"):
                users = msg.split(":")[1].split(",")

                user_list.delete(0, tk.END)

                for u in users:
                    user_list.insert(tk.END, u)

            else:
                chat.insert(tk.END, msg + "\n")

        except Exception as e:
            log(f"Receive error: {e}")
            break


def get_selected_user():
    selection = user_list.curselection()
    if selection:
        return user_list.get(selection[0])
    return None


def send():
    msg = entry.get()
    target = get_selected_user()

    if not msg:
        return

    try:
        if target:
            sock.send(f"PM:{target}:{msg}".encode())
            chat.insert(tk.END, f"[PM to {target}] {msg}\n")

        else:
            sock.send(f"MSG:{msg}".encode())
            chat.insert(tk.END, f"Me: {msg}\n")

    except Exception as e:
        chat.insert(tk.END, f"Send error: {e}\n")

    entry.delete(0, tk.END)


def toggle_tls():
    log("TLS toggled")
    connect()


# GUI
root = tk.Tk()
root.title("Chat")

# pytanie o nick
nickname = simpledialog.askstring("Nickname", "Enter nickname:", parent=root)

main_frame = tk.Frame(root)
main_frame.pack()

# lista użytkowników
user_list = tk.Listbox(main_frame, width=20)
user_list.pack(side=tk.LEFT, fill=tk.Y)

# czat
chat_frame = tk.Frame(main_frame)
chat_frame.pack(side=tk.RIGHT)

chat = tk.Text(chat_frame, height=15, width=50)
chat.pack()

entry = tk.Entry(chat_frame)
entry.pack()

send_btn = tk.Button(chat_frame, text="Send", command=send)
send_btn.pack()

tls_var = tk.BooleanVar()

tls_check = tk.Checkbutton(
    root,
    text="Use TLS",
    variable=tls_var,
    command=toggle_tls
)
tls_check.pack()

connect()

root.mainloop()