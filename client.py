import socket
import ssl
import threading
import tkinter as tk

HOST = "localhost"
PORT_PLAIN = 5000
PORT_TLS = 5001

sock = None

def connect():
    global sock

    use_tls = tls_var.get()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if use_tls:
        context = ssl.create_default_context(cafile="certs/cert.pem")
        sock = context.wrap_socket(sock, server_hostname=HOST)
        port = PORT_TLS
    else:
        port = PORT_PLAIN

    sock.connect((HOST, port))

    chat.insert(tk.END, f"Connected (TLS={use_tls})\n")

    threading.Thread(target=receive, daemon=True).start()

def receive():
    while True:
        try:
            msg = sock.recv(1024).decode()
            chat.insert(tk.END, msg + "\n")
        except:
            break

def send():
    msg = entry.get()
    sock.send(msg.encode())
    chat.insert(tk.END, f"Me: {msg}\n")
    entry.delete(0, tk.END)

root = tk.Tk()
root.title("Chat")

chat = tk.Text(root, height=15)
chat.pack()

entry = tk.Entry(root)
entry.pack()

send_btn = tk.Button(root, text="Send", command=send)
send_btn.pack()

tls_var = tk.BooleanVar()

tls_check = tk.Checkbutton(root, text="Use TLS", variable=tls_var)
tls_check.pack()

connect_btn = tk.Button(root, text="Connect", command=connect)
connect_btn.pack()

root.mainloop()