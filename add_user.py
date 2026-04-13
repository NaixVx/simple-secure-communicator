import hashlib
import getpass
import os

FILE = "users.txt"


def load_existing_users():
    users = set()
    if not os.path.exists(FILE):
        return users

    with open(FILE, "r") as f:
        for line in f:
            if ":" in line:
                user = line.split(":", 1)[0].strip()
                users.add(user)
    return users


def main():
    users = load_existing_users()

    username = input("Username: ").strip()
    if not username:
        print("Invalid username")
        return

    if username in users:
        print("User already exists")
        return

    password = getpass.getpass("Password: ").strip()
    confirm = getpass.getpass("Confirm password: ").strip()

    if password != confirm:
        print("Passwords do not match")
        return

    if not password:
        print("Empty password not allowed")
        return

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    with open(FILE, "a") as f:
        f.write(f"{username}:{pwd_hash}\n")

    print("User added successfully")


if __name__ == "__main__":
    main()