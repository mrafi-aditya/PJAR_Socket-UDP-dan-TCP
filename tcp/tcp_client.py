# tcp/tcp_client.py
import socket
import threading

SERVER_IP = "192.168.56.101"  # ganti dengan IP VirtualBox server
SERVER_PORT = 6000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

def receive_message():
    while True:
        try:
            message = client.recv(4096).decode()
            if not message:
                break
            print(message, end="")
        except:
            break

threading.Thread(target=receive_message, daemon=True).start()

while True:
    message = input()

    if message.startswith("/sendfile"):
        parts = message.split(" ", 1)

        if len(parts) < 2:
            print("Format: /sendfile path_file")
            continue

        filepath = parts[1]

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()

            filename = filepath.split("/")[-1]
            command = f"/sendfile {filename} {content}"
            client.send(command.encode())

        except FileNotFoundError:
            print("File tidak ditemukan.")

    else:
        client.send(message.encode())

    if message == "/quit":
        break

client.close()