import socket
import ssl
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import simpledialog

HOST = "localhost"

sock = None
nickname = None
current_chat = "GLOBAL"

chat_history = {
    "GLOBAL": []
}

def log(msg):
    print("[CLIENT]", msg)

def safe_insert(msg):
    root.after(0, lambda: (chat.insert("end", msg + "\n"), chat.see("end")))

def connect():
    global sock

    if sock:
        try:
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
        sock.connect((HOST, port))
        sock.send(f"NICK:{nickname}".encode())

        safe_insert(f"Connected as {nickname} TLS={use_tls}")

        threading.Thread(target=receive, daemon=True).start()

    except Exception as e:
        safe_insert(f"Connection error: {e}")

    refresh_chat()

def receive():
    global sock

    while True:
        try:
            data = sock.recv(1024)

            if not data:
                safe_insert("Disconnected from server")
                break

            msg = data.decode()

            if msg.startswith("USERS:"):
                users = msg.split(":")[1].split(",")

                def update_users():
                    user_list.delete(0, tk.END)
                    user_list.insert(tk.END, "GLOBAL")
                    for u in users:
                        if u != nickname:
                            user_list.insert(tk.END, u)

                root.after(0, update_users)

            elif msg.startswith("[PM from"):
                sender = msg.split("]")[0].split()[-1]

                if sender not in chat_history:
                    chat_history[sender] = []

                chat_history[sender].append(msg)

                if current_chat == sender:
                    safe_insert(msg)

            else:
                chat_history.setdefault("GLOBAL", []).append(msg)

                if current_chat == "GLOBAL":
                    safe_insert(msg)

        except:
            break

def select_chat(event):
    global current_chat

    selection = user_list.curselection()
    if not selection:
        return

    current_chat = user_list.get(selection[0])
    chat_label.configure(text=f"Chat: {current_chat}")
    refresh_chat()

def refresh_chat():
    chat.delete("1.0", "end")

    chat_history.setdefault(current_chat, [])

    for msg in chat_history[current_chat]:
        chat.insert("end", msg + "\n")

    chat.see("end")

def send(event=None):
    msg = entry.get()
    if not msg:
        return

    try:
        if current_chat == "GLOBAL":
            sock.send(f"MSG:{msg}".encode())
            chat_history["GLOBAL"].append(f"Me: {msg}")
        else:
            sock.send(f"PM:{current_chat}:{msg}".encode())
            chat_history.setdefault(current_chat, []).append(f"[PM to {current_chat}] {msg}")

        refresh_chat()

    except Exception as e:
        safe_insert(f"Send error: {e}")

    entry.delete(0, "end")

def toggle_tls():
    connect()

# GUI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Chat")

nickname = simpledialog.askstring("Nickname", "Enter nickname:", parent=root) or "Anonymous"

logged_label = ctk.CTkLabel(root, text=f"Logged as: {nickname}")
logged_label.pack()

main_frame = ctk.CTkFrame(root)
main_frame.pack()

user_list = tk.Listbox(main_frame, width=20)
user_list.bind("<<ListboxSelect>>", select_chat)
user_list.insert(tk.END, "GLOBAL")
user_list.pack(side="left", fill="y")

chat_frame = ctk.CTkFrame(main_frame)
chat_frame.pack(side="right")

chat_label = ctk.CTkLabel(chat_frame, text=f"Chat: {current_chat}")
chat_label.pack()

chat = ctk.CTkTextbox(chat_frame, width=500, height=300)
chat.pack()

entry = ctk.CTkEntry(chat_frame)
entry.pack()
entry.bind("<Return>", send)

send_btn = ctk.CTkButton(chat_frame, text="Send", command=send)
send_btn.pack()

tls_var = tk.BooleanVar()

tls_check = ctk.CTkCheckBox(root, text="Use TLS", variable=tls_var, command=toggle_tls)
tls_check.pack()

connect()
root.mainloop()