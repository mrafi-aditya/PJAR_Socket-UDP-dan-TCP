"""TCP Multi Client Chat Client.

Client ini tidak membutuhkan protocol.py. Setelah login, user cukup mengetik pesan biasa.
"""

import argparse
import base64
import getpass
import json
import shlex
import socket
import threading
from pathlib import Path

HOST_DEFAULT = "192.168.18.99"  # Ganti lewat --host jika IP Ubuntu VirtualBox berubah.
PORT_DEFAULT = 6000
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def send_json(sock, payload):
    """Mengirim satu paket JSON lewat TCP dengan pemisah newline."""
    data = json.dumps(payload, ensure_ascii=False) + "\n"
    sock.sendall(data.encode("utf-8"))


def read_json_line(reader):
    """Membaca satu baris JSON. Return None jika koneksi terputus."""
    line = reader.readline()
    if not line:
        return None
    return json.loads(line)


def print_server_message(payload):
    msg_type = payload.get("type", "info")
    text = payload.get("text", "")

    if msg_type == "error":
        print(f"\n[ERROR] {text}\n> ", end="")
    elif msg_type == "private":
        print(f"\n[PRIVATE] {text}\n> ", end="")
    else:
        print(f"\n{text}\n> ", end="")


def receive_messages(reader, stop_event):
    """Thread penerima pesan server agar user tetap bisa mengetik."""
    while not stop_event.is_set():
        try:
            payload = read_json_line(reader)
            if payload is None:
                print("\n[CLIENT] Koneksi server terputus.")
                stop_event.set()
                break
            print_server_message(payload)
        except json.JSONDecodeError:
            print("\n[CLIENT] Menerima data tidak valid dari server.")
        except OSError:
            stop_event.set()
            break
        except Exception as error:
            print(f"\n[CLIENT] Error menerima pesan: {error}")
            stop_event.set()
            break


def send_file(sock, filepath):
    """Membaca file lokal lalu mengirimnya ke server.

    Return True hanya jika paket file berhasil dikirim ke socket.
    Return False untuk kesalahan lokal, misalnya path salah, file kosong,
    atau file terlalu besar. Kesalahan lokal tidak boleh membuat client logout.
    """
    cleaned_path = (filepath or "").strip().strip('"').strip("'")
    if not cleaned_path:
        print("Format: /sendfile path_file")
        print("Contoh: /sendfile ../files/msg.txt")
        return False

    # Mencegah user menyalin teks bantuan secara utuh:
    # /sendfile path     : kirim file ke server
    if cleaned_path.lower().startswith("path") and ":" in cleaned_path:
        print("[CLIENT] Jangan ketik teks penjelasannya. Ganti 'path' dengan lokasi file asli.")
        print("Contoh: /sendfile ../files/msg.txt")
        return False

    path = Path(cleaned_path).expanduser()

    try:
        if not path.exists():
            print(f"[CLIENT] File tidak ditemukan: {cleaned_path}")
            print("Tips: jika terminal sedang di folder tcp, gunakan: /sendfile ../files/msg.txt")
            return False
        if not path.is_file():
            print(f"[CLIENT] Path bukan file: {cleaned_path}")
            return False

        size = path.stat().st_size
        if size == 0:
            print("[CLIENT] File kosong tidak dikirim.")
            return False
        if size > MAX_FILE_SIZE:
            print("[CLIENT] File terlalu besar. Maksimal 2 MB.")
            return False

        content_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError as error:
        print(f"[CLIENT] Gagal membaca file: {error}")
        return False

    try:
        send_json(sock, {
            "type": "file",
            "filename": path.name,
            "size": size,
            "content_b64": content_b64,
        })
    except OSError as error:
        print(f"[CLIENT] Gagal mengirim file ke server: {error}")
        return False

    print(f"[CLIENT] Mengirim file {path.name} ({size / 1024:.1f} KB).")
    return True


def run_client(host, port):
    stop_event = threading.Event()

    try:
        sock = socket.create_connection((host, port), timeout=10)
    except OSError as error:
        print(f"[CLIENT] Tidak bisa konek ke server {host}:{port}: {error}")
        return

    with sock:
        reader = sock.makefile("r", encoding="utf-8")

        try:
            welcome = read_json_line(reader)
            if welcome:
                print_server_message(welcome)
        except (json.JSONDecodeError, OSError):
            print("[CLIENT] Server mengirim data awal yang tidak valid.")
            return

        username = input("Username: ").strip()
        password = getpass.getpass("Password demo (123): ").strip()

        try:
            send_json(sock, {"type": "login", "username": username, "password": password})
            auth = read_json_line(reader)
        except (json.JSONDecodeError, OSError) as error:
            print(f"[CLIENT] Login gagal: {error}")
            return

        if not auth or auth.get("status") != "ok":
            reason = auth.get("text", "Login gagal.") if auth else "Server tidak merespons."
            print(f"[CLIENT] {reason}")
            return

        print(f"[CLIENT] {auth.get('text')}")
        print("Ketik /help untuk command. Ketik /quit untuk keluar.")

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
                elif message == "/sendfile":
                    print("Format: /sendfile path_file")
                    print("Contoh dari folder tcp: /sendfile ../files/msg.txt")
                elif message.startswith("/sendfile "):
                    # shlex membuat path yang memakai spasi bisa ditulis dengan tanda kutip.
                    # Contoh: /sendfile "../files/contoh file.txt"
                    try:
                        parts = shlex.split(message)
                    except ValueError as error:
                        print(f"[CLIENT] Format path tidak valid: {error}")
                        continue

                    if len(parts) != 2:
                        print("Format: /sendfile path_file")
                        print("Contoh: /sendfile ../files/msg.txt")
                        continue

                    send_file(sock, parts[1])
                elif message == "/quit":
                    send_json(sock, {"type": "quit"})
                    stop_event.set()
                    break
                else:
                    send_json(sock, {"type": "chat", "text": message})
            except KeyboardInterrupt:
                print("\n[CLIENT] Keluar dari TCP chat.")
                try:
                    send_json(sock, {"type": "quit"})
                except OSError:
                    pass
                stop_event.set()
                break
            except OSError as error:
                print(f"[CLIENT] Error mengirim data: {error}")
                stop_event.set()
                break


def main():
    parser = argparse.ArgumentParser(description="TCP Multi Client Chat Client")
    parser.add_argument("--host", default=HOST_DEFAULT, help="IP server Ubuntu VirtualBox")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="Port server, default 6000")
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
