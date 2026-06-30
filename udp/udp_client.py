"""UDP Chat Client.

Setelah memasukkan username, user cukup mengetik pesan biasa.
Client akan otomatis mengirim username ke server, jadi tidak perlu format "username: pesan".
"""

import argparse
import json
import re
import socket
import threading

HOST_DEFAULT = "192.168.18.99"  # Ganti lewat --host jika IP Ubuntu VirtualBox berubah.
PORT_DEFAULT = 5000
BUFFER_SIZE = 4096
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def is_valid_username(username):
    return bool(USERNAME_PATTERN.fullmatch(username or ""))


def make_packet(packet_type, **data):
    payload = {"type": packet_type}
    payload.update(data)
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def send_packet(sock, server_address, packet_type, **data):
    sock.sendto(make_packet(packet_type, **data), server_address)


def decode_server_message(data):
    """Decode pesan dari server. Jika bukan JSON, tetap ditampilkan sebagai teks biasa."""
    raw = data.decode("utf-8", errors="replace")
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload.get("type", "info"), str(payload.get("text", ""))
    except json.JSONDecodeError:
        pass
    return "info", raw


def print_message(msg_type, text):
    if msg_type == "error":
        print(f"\n[ERROR] {text}\n> ", end="")
    else:
        print(f"\n{text}\n> ", end="")


def receive_messages(sock, stop_event):
    """Thread untuk menerima pesan dari server sambil user mengetik."""
    while not stop_event.is_set():
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            msg_type, text = decode_server_message(data)
            print_message(msg_type, text)
        except OSError:
            break


def ask_username():
    username = input("Masukkan username (3-20 huruf/angka/_): ").strip()
    if not is_valid_username(username):
        print("[CLIENT] Username tidak valid. Contoh benar: Adit, user1, Rafi_01")
        return None
    return username


def run_client(host, port):
    username = ask_username()
    if not username:
        return

    server_address = (host, port)
    stop_event = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5)
        try:
            send_packet(sock, server_address, "join", username=username)
            data, _ = sock.recvfrom(BUFFER_SIZE)
            msg_type, text = decode_server_message(data)
            if msg_type == "error":
                print(f"[CLIENT] {text}")
                return
            print(text)
        except socket.timeout:
            print("[CLIENT] Server tidak merespons. Cek server, IP, port, dan firewall.")
            return
        except OSError as error:
            print(f"[CLIENT] Gagal menghubungi server: {error}")
            return

        sock.settimeout(None)
        threading.Thread(target=receive_messages, args=(sock, stop_event), daemon=True).start()

        print("\nCommand:")
        print("  /list  : lihat user online")
        print("  /quit  : keluar")
        print("  /help  : bantuan")
        print("\nKetik pesan biasa saja. Contoh: halo semuanya")
        print("Jangan pakai format username: pesan, karena username sudah otomatis.")

        while not stop_event.is_set():
            try:
                message = input("> ").strip()
                if not message:
                    print("[CLIENT] Pesan tidak boleh kosong.")
                    continue

                if message == "/help":
                    print("Command: /list, /quit, /help, atau langsung ketik isi pesan biasa.")
                elif message == "/list":
                    send_packet(sock, server_address, "list")
                elif message == "/quit":
                    send_packet(sock, server_address, "quit")
                    stop_event.set()
                    break
                else:
                    send_packet(sock, server_address, "chat", text=message)
            except KeyboardInterrupt:
                print("\n[CLIENT] Keluar dari UDP chat.")
                try:
                    send_packet(sock, server_address, "quit")
                except OSError:
                    pass
                stop_event.set()
                break
            except OSError as error:
                print(f"[CLIENT] Error mengirim pesan: {error}")
                stop_event.set()
                break


def main():
    parser = argparse.ArgumentParser(description="UDP Chat Client")
    parser.add_argument("--host", default=HOST_DEFAULT, help="IP server Ubuntu VirtualBox")
    parser.add_argument("--port", type=int, default=PORT_DEFAULT, help="Port server, default 5000")
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
