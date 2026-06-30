"""TCP Multi Client Chat Server untuk demo Socket Programming.

Server dijalankan di Ubuntu VirtualBox, client bisa dijalankan dari Windows/host.
File ini tidak membutuhkan protocol.py. Semua fungsi protocol JSON ada langsung di file ini.
"""

import argparse
import base64
import json
import logging
import re
import socket
import threading
from datetime import datetime
from pathlib import Path

HOST_DEFAULT = "0.0.0.0"
PORT_DEFAULT = 6000
MAX_MESSAGE_LENGTH = 1000
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB untuk demo agar aman.
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
LOGIN_PASSWORD = "123"

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

# clients: username -> {"sock": socket, "lock": threading.Lock(), "address": address}
clients = {}
clients_lock = threading.Lock()


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


def send_json(sock, payload):
    """Mengirim satu paket JSON lewat TCP.

    TCP adalah stream, jadi pesan dipisahkan dengan newline agar penerima tahu
    batas akhir satu paket.
    """
    data = json.dumps(payload, ensure_ascii=False) + "\n"
    sock.sendall(data.encode("utf-8"))


def read_json_line(reader):
    """Membaca satu baris JSON. Return None jika koneksi terputus."""
    line = reader.readline()
    if not line:
        return None
    return json.loads(line)


def is_valid_username(username):
    return bool(USERNAME_PATTERN.fullmatch(username or ""))


def safe_filename(filename):
    """Membersihkan nama file agar tidak bisa keluar dari folder tujuan."""
    name = Path(filename or "file_tanpa_nama").name.strip() or "file_tanpa_nama"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def send_to_user(username, payload):
    """Mengirim pesan ke user tertentu. Return True jika berhasil."""
    with clients_lock:
        record = clients.get(username)

    if not record:
        return False

    try:
        with record["lock"]:
            send_json(record["sock"], payload)
        return True
    except OSError as error:
        print(f"[ERROR] Gagal mengirim ke {username}: {error}")
        return False


def broadcast(payload, exclude=None):
    """Broadcast pesan ke semua client aktif."""
    with clients_lock:
        usernames = list(clients.keys())

    for username in usernames:
        if exclude is not None and username == exclude:
            continue
        send_to_user(username, payload)


def online_users():
    with clients_lock:
        return sorted(clients.keys())


def validate_login(username, password):
    """Login sederhana: username bebas yang valid, password demo adalah 123."""
    if not is_valid_username(username):
        return False, "Username harus 3-20 karakter dan hanya huruf/angka/underscore."
    if password != LOGIN_PASSWORD:
        return False, "Password salah. Password demo: 123"
    with clients_lock:
        if username in clients:
            return False, f"Username '{username}' sedang login di client lain."
    return True, "Login berhasil."


def handle_chat(username, text):
    clean_text = (text or "").strip()
    if not clean_text:
        send_to_user(username, {"type": "error", "text": "Pesan tidak boleh kosong."})
        return
    if len(clean_text) > MAX_MESSAGE_LENGTH:
        send_to_user(username, {"type": "error", "text": f"Pesan maksimal {MAX_MESSAGE_LENGTH} karakter."})
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {username}: {clean_text}"
    print(message)
    logging.info("TCP CHAT %s", message)
    broadcast({"type": "chat", "text": message})


def handle_private_message(username, target, text):
    target = (target or "").strip()
    clean_text = (text or "").strip()

    if not target or not clean_text:
        send_to_user(username, {"type": "error", "text": "Format: /msg username pesan"})
        return
    if target == username:
        send_to_user(username, {"type": "error", "text": "Tidak perlu mengirim private message ke diri sendiri."})
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    sent = send_to_user(target, {"type": "private", "text": f"[{timestamp}] [PM dari {username}] {clean_text}"})
    if sent:
        send_to_user(username, {"type": "info", "text": f"[PM ke {target}] {clean_text}"})
        logging.info("TCP PM %s -> %s: %s", username, target, clean_text)
    else:
        send_to_user(username, {"type": "error", "text": f"User '{target}' tidak online."})


def handle_file(username, payload):
    """Menerima file dari client dan menyimpannya.

    Semua error file dibalas ke client, bukan memutus koneksi client.
    """
    filename = safe_filename(str(payload.get("filename", "file.txt")))
    content_b64 = payload.get("content_b64", "")

    try:
        content = base64.b64decode(content_b64, validate=True)
    except (ValueError, TypeError):
        send_to_user(username, {"type": "error", "text": "File gagal dibaca: base64 tidak valid."})
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

    try:
        save_path.write_bytes(content)
    except OSError as error:
        send_to_user(username, {"type": "error", "text": f"Server gagal menyimpan file: {error}"})
        logging.exception("TCP gagal menyimpan file")
        return

    size_kb = len(content) / 1024
    info = f"File '{filename}' dari {username} tersimpan sebagai '{saved_name}' ({size_kb:.1f} KB)."
    print(f"[FILE] {info}")
    logging.info("TCP FILE %s", info)
    send_to_user(username, {"type": "info", "text": f"File berhasil dikirim: {saved_name}"})
    broadcast({"type": "info", "text": f"[SERVER] {username} mengirim file: {filename}"}, exclude=username)


def send_help(username):
    help_text = (
        "Command tersedia:\n"
        "  /help              : bantuan command\n"
        "  /list              : lihat user online\n"
        "  /msg user pesan    : kirim pesan private\n"
        "  /sendfile path     : kirim file ke server\n"
        "  /quit              : keluar dari chat"
    )
    send_to_user(username, {"type": "info", "text": help_text})


def cleanup_client(username):
    """Menghapus client dari daftar online."""
    if not username:
        return

    with clients_lock:
        record = clients.pop(username, None)

    if record:
        try:
            record["sock"].close()
        except OSError:
            pass

    broadcast({"type": "info", "text": f"[SERVER] {username} keluar dari TCP chat."}, exclude=username)
    logging.info("TCP LOGOUT %s", username)
    print(f"[LOGOUT] {username}")


def handle_client(conn, address):
    username = None
    try:
        reader = conn.makefile("r", encoding="utf-8")
        send_json(conn, {"type": "info", "text": "Silakan login. Username bebas, password demo: 123"})

        login_payload = read_json_line(reader)
        if not login_payload or login_payload.get("type") != "login":
            send_json(conn, {"type": "error", "text": "Payload login tidak valid."})
            return

        username = str(login_payload.get("username", "")).strip()
        password = str(login_payload.get("password", "")).strip()
        valid, message = validate_login(username, password)
        if not valid:
            send_json(conn, {"type": "auth", "status": "failed", "text": message})
            username = None
            return

        with clients_lock:
            clients[username] = {"sock": conn, "lock": threading.Lock(), "address": address}

        send_json(conn, {"type": "auth", "status": "ok", "text": message})
        send_help(username)
        broadcast({"type": "info", "text": f"[SERVER] {username} bergabung ke TCP chat."}, exclude=username)
        logging.info("TCP LOGIN %s dari %s", username, address)
        print(f"[LOGIN] {username} dari {address}")

        while True:
            try:
                payload = read_json_line(reader)
            except json.JSONDecodeError:
                send_to_user(username, {"type": "error", "text": "Format data tidak valid."})
                continue

            if payload is None:
                break

            msg_type = str(payload.get("type", "")).lower().strip()
            if msg_type == "chat":
                handle_chat(username, payload.get("text", ""))
            elif msg_type == "private":
                handle_private_message(username, payload.get("target", ""), payload.get("text", ""))
            elif msg_type == "list":
                send_to_user(username, {"type": "info", "text": "User online: " + (", ".join(online_users()) or "belum ada")})
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
        logging.exception("TCP client error")
    finally:
        cleanup_client(username)


def run_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(10)

        local_ip = get_local_ip()
        print("=" * 60)
        print(" TCP MULTI CLIENT CHAT SERVER")
        print("=" * 60)
        print(f"Bind address       : {host}:{port}")
        print(f"IP Ubuntu VBox     : {local_ip}")
        print(f"Client dari Windows: python tcp/tcp_client.py --host {local_ip} --port {port}")
        print("Login demo         : username bebas, password 123")
        print("Stop server        : CTRL + C")
        print("=" * 60)

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
                logging.exception("TCP server error")


def main():
    parser = argparse.ArgumentParser(description="TCP Multi Client Chat Server")
    parser.add_argument("--host", default=HOST_DEFAULT, help="Alamat bind server, default 0.0.0.0")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="Port server, default 6000")
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
