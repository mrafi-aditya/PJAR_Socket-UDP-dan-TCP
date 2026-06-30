"""UDP Broadcast Chat Server

Fitur:
- Menerima banyak client UDP.
- Broadcast pesan ke semua client aktif.
- Logging pesan ke file logs/udp_chat.log.
- Validasi username dan pesan.
"""

import argparse
import logging
import re
import socket
from datetime import datetime
from pathlib import Path

DEFAULT_HOST = "0.0.0.0"  # Server menerima koneksi dari semua interface jaringan.
DEFAULT_PORT = 5000
BUFFER_SIZE = 2048
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

clients: dict[tuple[str, int], str] = {}


def get_local_ip() -> str:
    """Mengambil IP lokal server agar mudah dipakai client dari Windows/host.

    Server tetap bind ke 0.0.0.0, sedangkan IP ini hanya ditampilkan
    supaya client tahu alamat Ubuntu VirtualBox yang harus dituju.
    """
    candidates: list[str] = []

    # Cara paling stabil untuk mengetahui IP interface aktif.
    for target in ("8.8.8.8", "1.1.1.1"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect((target, 80))
                candidates.append(probe.getsockname()[0])
        except OSError:
            pass

    # Cadangan jika cara di atas gagal.
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


def send(server: socket.socket, address: tuple[str, int], message: str) -> None:
    """Mengirim pesan UDP dengan error handling sederhana."""
    try:
        server.sendto(message.encode("utf-8"), address)
    except OSError as error:
        print(f"[ERROR] Gagal mengirim ke {address}: {error}")


def broadcast(server: socket.socket, message: str, exclude: tuple[str, int] | None = None) -> None:
    """Mengirim pesan ke semua client, kecuali alamat tertentu jika ada."""
    for address in list(clients.keys()):
        if address == exclude:
            continue
        send(server, address, message)


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.match(username))


def handle_join(server: socket.socket, address: tuple[str, int], username: str) -> None:
    """Mendaftarkan client baru ke daftar client aktif."""
    if not is_valid_username(username):
        send(server, address, "[SERVER] Username harus 3-20 karakter, hanya huruf/angka/underscore.")
        return

    clients[address] = username
    send(server, address, f"[SERVER] Berhasil bergabung sebagai {username}.")
    broadcast(server, f"[SERVER] {username} bergabung ke UDP chat.", exclude=address)
    logging.info("JOIN %s %s", username, address)
    print(f"[JOIN] {username} dari {address}")


def handle_message(server: socket.socket, address: tuple[str, int], username: str, text: str) -> None:
    """Memvalidasi pesan, menyimpan log, lalu broadcast."""
    if address not in clients:
        send(server, address, "[SERVER] Anda belum join. Jalankan ulang client atau masukkan username.")
        return

    if clients[address] != username:
        send(server, address, "[SERVER] Username tidak sesuai dengan alamat client.")
        return

    if not text.strip():
        send(server, address, "[SERVER] Pesan tidak boleh kosong.")
        return

    if len(text) > MAX_MESSAGE_LENGTH:
        send(server, address, f"[SERVER] Pesan maksimal {MAX_MESSAGE_LENGTH} karakter.")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {username}: {text.strip()}"
    logging.info("CHAT %s %s", address, formatted)
    print(formatted)
    broadcast(server, formatted, exclude=address)


def handle_list(server: socket.socket, address: tuple[str, int]) -> None:
    """Menampilkan daftar user UDP yang aktif."""
    online = sorted(set(clients.values()))
    send(server, address, "[SERVER] User online: " + (", ".join(online) if online else "belum ada"))


def handle_quit(server: socket.socket, address: tuple[str, int]) -> None:
    """Menghapus client dari daftar aktif."""
    username = clients.pop(address, None)
    if username:
        send(server, address, "[SERVER] Anda keluar dari UDP chat.")
        broadcast(server, f"[SERVER] {username} keluar dari UDP chat.", exclude=address)
        logging.info("QUIT %s %s", username, address)
        print(f"[QUIT] {username} dari {address}")


def parse_packet(packet: str) -> tuple[str, list[str]]:
    """Format paket: JOIN|username, MSG|username|pesan, LIST, QUIT."""
    parts = packet.strip().split("|", 2)
    command = parts[0].upper() if parts else ""
    return command, parts[1:]


def run_server(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind((host, port))
        print("=" * 55)
        print(" UDP BROADCAST CHAT SERVER")
        print("=" * 55)
        local_ip = get_local_ip()
        print(f"Bind address       : {host}:{port}")
        print(f"IP Ubuntu VBox     : {local_ip}")
        print(f"Client dari Windows: python udp/udp_client.py --host {local_ip} --port {port}")
        print("Client di server   : python udp/udp_client.py --host 127.0.0.1")
        print("Stop server        : CTRL + C")
        print("=" * 55)

        while True:
            try:
                data, address = server.recvfrom(BUFFER_SIZE)
                packet = data.decode("utf-8", errors="replace").strip()
                command, args = parse_packet(packet)

                if command == "JOIN" and len(args) == 1:
                    handle_join(server, address, args[0].strip())
                elif command == "MSG" and len(args) == 2:
                    handle_message(server, address, args[0].strip(), args[1])
                elif command == "LIST":
                    handle_list(server, address)
                elif command == "QUIT":
                    handle_quit(server, address)
                else:
                    send(server, address, "[SERVER] Format tidak valid. Gunakan client resmi atau command /help.")
            except UnicodeDecodeError:
                send(server, address, "[SERVER] Data harus berupa teks UTF-8.")
            except KeyboardInterrupt:
                print("\n[SERVER] UDP server dihentikan.")
                break
            except OSError as error:
                print(f"[ERROR] Socket error: {error}")
                logging.exception("Socket error")


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP Broadcast Chat Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Alamat bind server, default 0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port server, default 5000")
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
