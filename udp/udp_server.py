"""UDP Chat Server untuk demo Socket Programming.

Server dijalankan di Ubuntu VirtualBox, client bisa dijalankan dari Windows/host.
Format komunikasi internal menggunakan JSON, jadi user client cukup mengetik pesan biasa.
"""

import argparse
import json
import logging
import re
import socket
from datetime import datetime
from pathlib import Path

HOST_DEFAULT = "0.0.0.0"
PORT_DEFAULT = 5000
BUFFER_SIZE = 4096
MAX_MESSAGE_LENGTH = 500
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "udp_chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# clients menyimpan alamat UDP client dan username-nya.
# Contoh key: ('192.168.18.10', 53001), value: 'Adit'
clients = {}


def get_local_ip():
    """Mencoba menampilkan IP aktif server agar mudah dipakai client."""
    candidates = []
    for target in ("8.8.8.8", "1.1.1.1"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((target, 80))
                candidates.append(sock.getsockname()[0])
        except OSError:
            pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            candidates.append(info[4][0])
    except OSError:
        pass

    for ip_address in candidates:
        if ip_address and not ip_address.startswith("127."):
            return ip_address
    return "127.0.0.1"


def is_valid_username(username):
    """Username hanya boleh huruf, angka, dan underscore."""
    return bool(USERNAME_PATTERN.fullmatch(username or ""))


def make_packet(packet_type, text, **extra):
    """Membuat paket JSON yang akan dikirim ke client."""
    payload = {"type": packet_type, "text": text}
    payload.update(extra)
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def send_packet(server, address, packet_type, text, **extra):
    """Mengirim paket ke satu client dengan error handling."""
    try:
        server.sendto(make_packet(packet_type, text, **extra), address)
    except OSError as error:
        print(f"[ERROR] Gagal mengirim ke {address}: {error}")


def broadcast(server, packet_type, text, exclude=None, **extra):
    """Mengirim pesan ke semua client yang sudah join."""
    for address in list(clients.keys()):
        if exclude is not None and address == exclude:
            continue
        send_packet(server, address, packet_type, text, **extra)


def decode_packet(data):
    """Decode data UDP dari client. Hanya menerima format JSON."""
    try:
        packet = json.loads(data.decode("utf-8"))
        if not isinstance(packet, dict):
            return None, "Paket harus berupa JSON object."
        return packet, None
    except UnicodeDecodeError:
        return None, "Encoding paket tidak valid."
    except json.JSONDecodeError:
        return None, "Format paket tidak valid. Gunakan client UDP resmi."


def username_already_used(username, current_address=None):
    """Mencegah dua client memakai username yang sama."""
    for address, active_username in clients.items():
        if address != current_address and active_username == username:
            return True
    return False


def handle_join(server, address, username):
    username = (username or "").strip()

    if not is_valid_username(username):
        send_packet(server, address, "error", "Username harus 3-20 karakter dan hanya huruf/angka/underscore.")
        return

    if username_already_used(username, current_address=address):
        send_packet(server, address, "error", f"Username '{username}' sedang dipakai client lain.")
        return

    old_username = clients.get(address)
    clients[address] = username

    if old_username and old_username != username:
        send_packet(server, address, "info", f"Username diganti dari {old_username} menjadi {username}.")
        logging.info("UDP REJOIN %s -> %s dari %s", old_username, username, address)
        return

    send_packet(server, address, "info", f"Berhasil bergabung sebagai {username}.")
    broadcast(server, "info", f"[SERVER] {username} bergabung ke UDP chat.", exclude=address)
    logging.info("UDP JOIN %s dari %s", username, address)
    print(f"[JOIN] {username} dari {address}")


def handle_chat(server, address, text):
    username = clients.get(address)
    if not username:
        send_packet(server, address, "error", "Kamu belum join. Jalankan ulang client lalu masukkan username.")
        return

    clean_text = (text or "").strip()
    if not clean_text:
        send_packet(server, address, "error", "Pesan tidak boleh kosong.")
        return

    if len(clean_text) > MAX_MESSAGE_LENGTH:
        send_packet(server, address, "error", f"Pesan maksimal {MAX_MESSAGE_LENGTH} karakter.")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {username}: {clean_text}"
    print(message)
    logging.info("UDP CHAT %s", message)
    broadcast(server, "chat", message)


def handle_list(server, address):
    online = sorted(set(clients.values()))
    text = "User online: " + (", ".join(online) if online else "belum ada")
    send_packet(server, address, "info", text)


def handle_quit(server, address):
    username = clients.pop(address, None)
    if username:
        send_packet(server, address, "info", "Kamu keluar dari UDP chat.")
        broadcast(server, "info", f"[SERVER] {username} keluar dari UDP chat.", exclude=address)
        logging.info("UDP QUIT %s dari %s", username, address)
        print(f"[QUIT] {username} dari {address}")
    else:
        send_packet(server, address, "info", "Client belum terdaftar.")


def handle_packet(server, address, packet):
    packet_type = str(packet.get("type", "")).lower().strip()

    if packet_type == "join":
        handle_join(server, address, packet.get("username", ""))
    elif packet_type == "chat":
        handle_chat(server, address, packet.get("text", ""))
    elif packet_type == "list":
        handle_list(server, address)
    elif packet_type == "quit":
        handle_quit(server, address)
    else:
        send_packet(server, address, "error", "Command tidak dikenali. Gunakan /help di client.")


def run_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((host, port))
        local_ip = get_local_ip()

        print("=" * 60)
        print(" UDP CHAT SERVER")
        print("=" * 60)
        print(f"Bind address       : {host}:{port}")
        print(f"IP Ubuntu VBox     : {local_ip}")
        print(f"Client dari Windows: python udp/udp_client.py --host {local_ip} --port {port}")
        print("Stop server        : CTRL + C")
        print("=" * 60)

        while True:
            try:
                data, address = server.recvfrom(BUFFER_SIZE)
                packet, error = decode_packet(data)
                if error:
                    send_packet(server, address, "error", error)
                    continue
                handle_packet(server, address, packet)
            except KeyboardInterrupt:
                print("\n[SERVER] UDP server dihentikan.")
                break
            except OSError as error:
                print(f"[ERROR] Socket error: {error}")
                logging.exception("UDP socket error")


def main():
    parser = argparse.ArgumentParser(description="UDP Chat Server")
    parser.add_argument("--host", default=HOST_DEFAULT, help="Alamat bind server, default 0.0.0.0")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="Port server, default 5000")
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
