"""TCP Multi Client Chat Client.

Default host menggunakan 127.0.0.1 agar tidak bergantung pada IP VirtualBox.
Untuk beda laptop/jaringan, jalankan client dengan --host IP_SERVER.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import socket
import threading
from pathlib import Path

from protocol import read_json_line, send_json

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6000
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def print_server_message(payload: dict) -> None:
    """Menampilkan pesan server dengan format CLI yang rapi."""
    msg_type = payload.get("type", "info")
    text = payload.get("text", "")

    if msg_type == "error":
        prefix = "[ERROR]"
    elif msg_type == "private":
        prefix = "[PRIVATE]"
    elif msg_type == "chat":
        prefix = ""
    else:
        prefix = "[INFO]"

    if prefix:
        print(f"\n{prefix} {text}\n> ", end="")
    else:
        print(f"\n{text}\n> ", end="")


def receive_messages(reader, stop_event: threading.Event) -> None:
    """Thread penerima pesan dari server."""
    while not stop_event.is_set():
        try:
            payload = read_json_line(reader)
            if payload is None:
                print("\n[CLIENT] Koneksi server terputus.")
                stop_event.set()
                break
            print_server_message(payload)
        except Exception as error:
            print(f"\n[CLIENT] Error menerima pesan: {error}")
            stop_event.set()
            break


def send_file(sock: socket.socket, filepath: str) -> None:
    """Membaca file lokal dan mengirimkannya ke server."""
    path = Path(filepath).expanduser()

    if not path.is_file():
        print("[CLIENT] File tidak ditemukan.")
        return

    size = path.stat().st_size
    if size == 0:
        print("[CLIENT] File kosong tidak dikirim.")
        return
    if size > MAX_FILE_SIZE:
        print("[CLIENT] File terlalu besar. Maksimal 2 MB.")
        return

    content_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    send_json(sock, {
        "type": "file",
        "filename": path.name,
        "size": size,
        "content_b64": content_b64,
    })
    print(f"[CLIENT] Mengirim file {path.name} ({size / 1024:.1f} KB).")


def run_client(host: str, port: int) -> None:
    stop_event = threading.Event()

    try:
        sock = socket.create_connection((host, port), timeout=10)
    except OSError as error:
        print(f"[CLIENT] Tidak bisa konek ke server {host}:{port}: {error}")
        return

    with sock:
        reader = sock.makefile("r", encoding="utf-8")

        welcome = read_json_line(reader)
        if welcome:
            print_server_message(welcome)

        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        send_json(sock, {"type": "login", "username": username, "password": password})

        auth = read_json_line(reader)
        if not auth or auth.get("status") != "ok":
            reason = auth.get("text", "Login gagal.") if auth else "Server tidak merespons."
            print(f"[CLIENT] {reason}")
            return

        print(f"[CLIENT] {auth.get('text')}")
        print("Ketik /help untuk melihat command. Ketik /quit untuk keluar.")

        threading.Thread(target=receive_messages, args=(reader, stop_event), daemon=True).start()

        while not stop_event.is_set():
            try:
                message = input("> ").strip()

                if not message:
                    print("[CLIENT] Pesan tidak boleh kosong.")
                    continue

                if message == "/help":
                    send_json(sock, {"type": "help"})
                elif message == "/list":
                    send_json(sock, {"type": "list"})
                elif message.startswith("/msg "):
                    parts = message.split(" ", 2)
                    if len(parts) < 3:
                        print("Format: /msg username pesan")
                    else:
                        send_json(sock, {"type": "private", "target": parts[1], "text": parts[2]})
                elif message.startswith("/sendfile "):
                    filepath = message.split(" ", 1)[1].strip().strip('"')
                    send_file(sock, filepath)
                elif message == "/quit":
                    send_json(sock, {"type": "quit"})
                    stop_event.set()
                    break
                else:
                    send_json(sock, {"type": "chat", "text": message})
            except KeyboardInterrupt:
                print("\n[CLIENT] Keluar dari TCP chat.")
                send_json(sock, {"type": "quit"})
                stop_event.set()
                break
            except OSError as error:
                print(f"[CLIENT] Error mengirim data: {error}")
                stop_event.set()
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="TCP Multi Client Chat Client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="IP server, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port server, default 6000")
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
