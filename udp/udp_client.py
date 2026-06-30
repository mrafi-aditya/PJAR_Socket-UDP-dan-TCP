"""UDP Broadcast Chat Client.

Default host menggunakan 127.0.0.1 agar mudah demo di laptop sendiri,
bukan IP VirtualBox. Jika beda device, isi dengan IP lokal server.
"""

import argparse
import re
import socket
import threading

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
BUFFER_SIZE = 2048
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.match(username))


def receive_messages(client: socket.socket, stop_event: threading.Event) -> None:
    """Thread penerima pesan dari server."""
    while not stop_event.is_set():
        try:
            data, _ = client.recvfrom(BUFFER_SIZE)
            print(f"\n{data.decode('utf-8', errors='replace')}\n> ", end="")
        except OSError:
            break


def run_client(host: str, port: int) -> None:
    username = input("Masukkan username (3-20 huruf/angka/_): ").strip()
    if not is_valid_username(username):
        print("[CLIENT] Username tidak valid.")
        return

    server_address = (host, port)
    stop_event = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(1.0)

        try:
            client.sendto(f"JOIN|{username}".encode("utf-8"), server_address)
            data, _ = client.recvfrom(BUFFER_SIZE)
            print(data.decode("utf-8", errors="replace"))
        except socket.timeout:
            print("[CLIENT] Server tidak merespons. Pastikan UDP server sudah berjalan.")
            return
        except OSError as error:
            print(f"[CLIENT] Gagal konek ke server: {error}")
            return

        client.settimeout(None)
        threading.Thread(target=receive_messages, args=(client, stop_event), daemon=True).start()

        print("\nCommand:")
        print("  /list  : lihat user online")
        print("  /quit  : keluar")
        print("  /help  : bantuan")
        print("Ketik pesan biasa untuk broadcast UDP. Format server: username: pesan")

        while True:
            try:
                message = input("> ").strip()

                if not message:
                    print("[CLIENT] Pesan tidak boleh kosong.")
                    continue

                if message == "/help":
                    print("Command: /list, /quit, atau ketik pesan biasa.")
                    continue

                if message == "/list":
                    client.sendto(b"LIST", server_address)
                    continue

                if message == "/quit":
                    client.sendto(b"QUIT", server_address)
                    stop_event.set()
                    break

                client.sendto(f"MSG|{username}|{message}".encode("utf-8"), server_address)
            except KeyboardInterrupt:
                client.sendto(b"QUIT", server_address)
                stop_event.set()
                print("\n[CLIENT] Keluar dari UDP chat.")
                break
            except OSError as error:
                print(f"[CLIENT] Error mengirim pesan: {error}")
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP Broadcast Chat Client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="IP server, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port server, default 5000")
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
