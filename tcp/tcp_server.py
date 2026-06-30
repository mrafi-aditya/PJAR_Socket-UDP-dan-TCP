"""TCP Multi Client Chat Server.

Fitur:
- Multi-client dengan threading.
- Login username/password.
- Chat real-time.
- Command /list, /msg, /help, /quit.
- Terima file dari client dan simpan ke folder received_files.
- Logging ke logs/tcp_chat.log.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import re
import socket
import threading
from datetime import datetime
from pathlib import Path




def send_json(sock: socket.socket, payload: dict) -> None:
    """Mengirim data JSON lewat TCP tanpa file protocol.py.

    TCP tidak punya batas pesan seperti UDP, jadi setiap JSON diakhiri newline.
    Newline dipakai sebagai pemisah antar pesan agar penerima mudah membaca
    satu pesan utuh per baris.
    """
    data = json.dumps(payload, ensure_ascii=False) + "\n"
    sock.sendall(data.encode("utf-8"))


def read_json_line(reader):
    """Membaca satu baris JSON dari koneksi TCP.

    Return None jika koneksi client/server terputus.
    """
    line = reader.readline()
    if not line:
        return None
    return json.loads(line)


DEFAULT_HOST = "0.0.0.0"  # Server menerima koneksi dari semua interface jaringan.
DEFAULT_PORT = 6000
MAX_MESSAGE_LENGTH = 1000
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB agar aman untuk demo tugas.
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
RECEIVED_DIR = BASE_DIR / "received_files"
LOG_DIR.mkdir(exist_ok=True)
RECEIVED_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "tcp_chat.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

USERS = {
    "admin": "123",
    "user1": "123",
    "user2": "123",
}

clients: dict[str, socket.socket] = {}
client_addresses: dict[str, tuple[str, int]] = {}
clients_lock = threading.Lock()


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


def safe_filename(filename: str) -> str:
    """Membersihkan nama file agar tidak bisa keluar dari folder tujuan."""
    name = Path(filename).name.strip() or "file_tanpa_nama"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def send_to_user(username: str, payload: dict) -> bool:
    """Mengirim payload ke user tertentu."""
    with clients_lock:
        sock = clients.get(username)
    if not sock:
        return False
    try:
        send_json(sock, payload)
        return True
    except OSError as error:
        print(f"[ERROR] Gagal mengirim ke {username}: {error}")
        return False


def broadcast(payload: dict, exclude: str | None = None) -> None:
    """Broadcast pesan ke semua client aktif."""
    with clients_lock:
        online = list(clients.items())

    for username, sock in online:
        if username == exclude:
            continue
        try:
            send_json(sock, payload)
        except OSError as error:
            print(f"[ERROR] Broadcast gagal ke {username}: {error}")


def online_users() -> list[str]:
    with clients_lock:
        return sorted(clients.keys())


def validate_login(username: str, password: str) -> tuple[bool, str]:
    """Validasi login sederhana."""
    if not USERNAME_PATTERN.match(username):
        return False, "Username harus 3-20 karakter, hanya huruf/angka/underscore."
    if USERS.get(username) != password:
        return False, "Username atau password salah."
    with clients_lock:
        if username in clients:
            return False, "Username sedang login di client lain."
    return True, "Login berhasil."


def handle_chat(username: str, text: str) -> None:
    """Memproses chat biasa dari client."""
    text = text.strip()
    if not text:
        send_to_user(username, {"type": "error", "text": "Pesan tidak boleh kosong."})
        return
    if len(text) > MAX_MESSAGE_LENGTH:
        send_to_user(username, {"type": "error", "text": f"Pesan maksimal {MAX_MESSAGE_LENGTH} karakter."})
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {username}: {text}"
    print(message)
    logging.info("CHAT %s", message)
    broadcast({"type": "chat", "text": message})


def handle_private_message(username: str, target: str, text: str) -> None:
    """Mengirim pesan private antar user."""
    if not target or not text.strip():
        send_to_user(username, {"type": "error", "text": "Format: /msg username pesan"})
        return
    if target == username:
        send_to_user(username, {"type": "error", "text": "Tidak perlu mengirim private message ke diri sendiri."})
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    sent = send_to_user(target, {"type": "private", "text": f"[{timestamp}] [PM dari {username}] {text.strip()}"})
    if sent:
        send_to_user(username, {"type": "info", "text": f"[PM ke {target}] {text.strip()}"})
        logging.info("PM %s -> %s: %s", username, target, text.strip())
    else:
        send_to_user(username, {"type": "error", "text": f"User {target} tidak online."})


def handle_file(username: str, payload: dict) -> None:
    """Menerima file base64 dari client lalu menyimpannya."""
    filename = safe_filename(str(payload.get("filename", "file.txt")))
    content_b64 = payload.get("content_b64", "")

    try:
        content = base64.b64decode(content_b64, validate=True)
    except (ValueError, TypeError):
        send_to_user(username, {"type": "error", "text": "File gagal dibaca: format base64 tidak valid."})
        return

    if len(content) == 0:
        send_to_user(username, {"type": "error", "text": "File kosong tidak dikirim."})
        return
    if len(content) > MAX_FILE_SIZE:
        send_to_user(username, {"type": "error", "text": "Ukuran file melebihi 2 MB."})
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_name = f"{timestamp}_{username}_{filename}"
    save_path = RECEIVED_DIR / saved_name
    save_path.write_bytes(content)

    size_kb = len(content) / 1024
    info = f"File '{filename}' dari {username} tersimpan sebagai '{saved_name}' ({size_kb:.1f} KB)."
    print(f"[FILE] {info}")
    logging.info("FILE %s", info)
    send_to_user(username, {"type": "info", "text": f"File berhasil dikirim: {saved_name}"})
    broadcast({"type": "info", "text": f"[SERVER] {username} mengirim file: {filename}"}, exclude=username)


def send_help(username: str) -> None:
    """Mengirim daftar command ke client."""
    help_text = (
        "Command tersedia:\n"
        "  /help              : bantuan command\n"
        "  /list              : lihat user online\n"
        "  /msg user pesan    : kirim pesan private\n"
        "  /sendfile path     : kirim file ke server\n"
        "  /quit              : keluar dari chat"
    )
    send_to_user(username, {"type": "info", "text": help_text})


def cleanup_client(username: str | None) -> None:
    """Menghapus client saat disconnect."""
    if not username:
        return
    with clients_lock:
        sock = clients.pop(username, None)
        client_addresses.pop(username, None)
    if sock:
        try:
            sock.close()
        except OSError:
            pass
    broadcast({"type": "info", "text": f"[SERVER] {username} keluar dari TCP chat."}, exclude=username)
    logging.info("LOGOUT %s", username)
    print(f"[LOGOUT] {username}")


def handle_client(conn: socket.socket, address: tuple[str, int]) -> None:
    """Thread handler untuk satu client TCP."""
    username: str | None = None
    try:
        reader = conn.makefile("r", encoding="utf-8")
        send_json(conn, {"type": "info", "text": "Silakan login menggunakan username dan password."})

        login_payload = read_json_line(reader)
        if not login_payload or login_payload.get("type") != "login":
            send_json(conn, {"type": "error", "text": "Payload login tidak valid."})
            return

        username = str(login_payload.get("username", "")).strip()
        password = str(login_payload.get("password", "")).strip()
        valid, message = validate_login(username, password)
        if not valid:
            send_json(conn, {"type": "auth", "status": "failed", "text": message})
            return

        with clients_lock:
            clients[username] = conn
            client_addresses[username] = address

        send_json(conn, {"type": "auth", "status": "ok", "text": message})
        send_help(username)
        broadcast({"type": "info", "text": f"[SERVER] {username} bergabung ke TCP chat."}, exclude=username)
        logging.info("LOGIN %s %s", username, address)
        print(f"[LOGIN] {username} dari {address}")

        while True:
            try:
                payload = read_json_line(reader)
            except json.JSONDecodeError:
                send_to_user(username, {"type": "error", "text": "Format data tidak valid."})
                continue

            if payload is None:
                break

            msg_type = payload.get("type")
            if msg_type == "chat":
                handle_chat(username, str(payload.get("text", "")))
            elif msg_type == "private":
                handle_private_message(username, str(payload.get("target", "")).strip(), str(payload.get("text", "")))
            elif msg_type == "list":
                send_to_user(username, {"type": "info", "text": "User online: " + ", ".join(online_users())})
            elif msg_type == "help":
                send_help(username)
            elif msg_type == "file":
                handle_file(username, payload)
            elif msg_type == "quit":
                send_to_user(username, {"type": "info", "text": "Keluar dari TCP chat."})
                break
            else:
                send_to_user(username, {"type": "error", "text": "Command tidak dikenali. Ketik /help."})
    except ConnectionResetError:
        print(f"[DISCONNECT] Client {address} terputus tiba-tiba.")
    except OSError as error:
        print(f"[ERROR] Client {address}: {error}")
        logging.exception("Client error")
    finally:
        cleanup_client(username)


def run_server(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(10)

        print("=" * 55)
        print(" TCP MULTI CLIENT CHAT SERVER")
        print("=" * 55)
        local_ip = get_local_ip()
        print(f"Bind address       : {host}:{port}")
        print(f"IP Ubuntu VBox     : {local_ip}")
        print(f"Client dari Windows: python tcp/tcp_client.py --host {local_ip} --port {port}")
        print("Client di server   : python tcp/tcp_client.py --host 127.0.0.1")
        print("Akun demo          : admin/123, user1/123, user2/123")
        print("Stop server        : CTRL + C")
        print("=" * 55)

        while True:
            try:
                conn, address = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, address), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                print("\n[SERVER] TCP server dihentikan.")
                break
            except OSError as error:
                print(f"[ERROR] Server error: {error}")
                logging.exception("Server error")


def main() -> None:
    parser = argparse.ArgumentParser(description="TCP Multi Client Chat Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Alamat bind server, default 0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port server, default 6000")
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
