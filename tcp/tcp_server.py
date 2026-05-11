# tcp/tcp_server.py
import socket
import threading
import os

HOST = "0.0.0.0"
PORT = 6000

users = {
    "admin": "123",
    "user1": "123",
    "user2": "123"
}

clients = {}

def broadcast(message, sender_socket=None):
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                client_socket.send(message.encode())
            except:
                pass

def handle_client(client_socket, address):
    try:
        client_socket.send("Username:\n".encode())
        username = client_socket.recv(1024).decode().strip()

        client_socket.send("Password:\n".encode())
        password = client_socket.recv(1024).decode().strip()

        if username not in users or users[username] != password:
            client_socket.send("Login gagal.\n".encode())
            client_socket.close()
            return

        clients[client_socket] = username
        client_socket.send("Login berhasil.\n".encode())

        print(f"[LOGIN] {username} dari {address}")
        broadcast(f"[SERVER] {username} bergabung ke chat.\n", client_socket)

        while True:
            message = client_socket.recv(4096).decode().strip()

            if not message:
                break

            if message == "/quit":
                break

            elif message == "/list":
                online_users = ", ".join(clients.values())
                client_socket.send(f"User online: {online_users}\n".encode())

            elif message.startswith("/sendfile"):
                parts = message.split(" ", 2)

                if len(parts) < 3:
                    client_socket.send("Format: /sendfile nama_file isi_file\n".encode())
                    continue

                filename = parts[1]
                content = parts[2]

                os.makedirs("received_files", exist_ok=True)
                filepath = os.path.join("received_files", filename)

                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(content)

                client_socket.send(f"File {filename} berhasil dikirim ke server.\n".encode())
                print(f"[FILE] {username} mengirim {filename}")

            else:
                chat_message = f"{username}: {message}\n"
                print(chat_message.strip())
                broadcast(chat_message, client_socket)

    except Exception as e:
        print(f"[ERROR] {address}: {e}")

    finally:
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]
            broadcast(f"[SERVER] {username} keluar dari chat.\n")

        client_socket.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"[TCP SERVER] Running on {HOST}:{PORT}")

while True:
    client_socket, address = server.accept()
    thread = threading.Thread(target=handle_client, args=(client_socket, address))
    thread.start()