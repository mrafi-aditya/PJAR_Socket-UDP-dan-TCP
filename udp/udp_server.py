# udp/udp_server.py
import socket
import logging

HOST = "0.0.0.0"
PORT = 5000

clients = set()

logging.basicConfig(
    filename="udp_chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"[UDP SERVER] Running on {HOST}:{PORT}")

while True:
    try:
        data, address = server.recvfrom(1024)
        message = data.decode().strip()

        if not message:
            server.sendto("Pesan tidak boleh kosong.".encode(), address)
            continue

        clients.add(address)

        if ":" not in message:
            server.sendto("Format salah. Gunakan username: pesan".encode(), address)
            continue

        print(f"[{address}] {message}")
        logging.info(f"{address} - {message}")

        for client in clients:
            if client != address:
                server.sendto(message.encode(), client)

    except Exception as e:
        print(f"[ERROR] {e}")