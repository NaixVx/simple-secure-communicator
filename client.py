import socket
import ssl
import threading
import tkinter as tk

HOST = "localhost"

sock = None

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

        chat.insert(tk.END, f"Connected TLS={use_tls}, port={port}\n")

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

            chat.insert(tk.END, msg + "\n")

        except Exception as e:
            log(f"Receive error: {e}")
            break


def send():
    global sock

    msg = entry.get()

    try:
        log(f"Sending: {msg}")
        sock.send(msg.encode())

        chat.insert(tk.END, f"Me: {msg}\n")

    except Exception as e:
        log(f"Send error: {e}")
        chat.insert(tk.END, f"Send error: {e}\n")

    entry.delete(0, tk.END)


def toggle_tls():
    log("TLS toggled")
    connect()


root = tk.Tk()
root.title("Chat")

chat = tk.Text(root, height=15)
chat.pack()

entry = tk.Entry(root)
entry.pack()

send_btn = tk.Button(root, text="Send", command=send)
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