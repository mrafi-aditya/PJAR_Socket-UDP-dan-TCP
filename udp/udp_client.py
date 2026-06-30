"""UDP Broadcast Chat Client.

Skenario penggunaan:
- Server UDP dijalankan di Ubuntu VirtualBox.
- Client UDP bisa dijalankan dari Windows/host atau Ubuntu.
- Setelah memasukkan username, user cukup mengetik isi pesan saja.
"""

import argparse
import re
import socket
import threading

DEFAULT_HOST = "192.168.18.9"  # IP Ubuntu VirtualBox. Ubah via --host jika IP berubah.
DEFAULT_PORT = 5000
BUFFER_SIZE = 2048
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def is_valid_username(username: str) -> bool:
    """Validasi username agar rapi dan aman untuk ditampilkan di chat."""
    return bool(USERNAME_PATTERN.fullmatch(username))


def receive_messages(client: socket.socket, stop_event: threading.Event) -> None:
    """Menerima pesan dari server secara paralel agar client tetap bisa mengetik."""
    while not stop_event.is_set():
        try:
            data, _ = client.recvfrom(BUFFER_SIZE)
            message = data.decode("utf-8", errors="replace")
            print(f"\n{message}\n> ", end="")
        except OSError:
            break


def run_client(host: str, port: int) -> None:
    username = input("Masukkan username (3-20 huruf/angka/_): ").strip()
    if not is_valid_username(username):
        print("[CLIENT] Username tidak valid. Gunakan 3-20 huruf/angka/underscore.")
        return

    server_address = (host, port)
    stop_event = threading.Event()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        # Timeout hanya dipakai saat proses JOIN agar tidak menunggu selamanya.
        client.settimeout(3.0)

        try:
            client.sendto(f"JOIN|{username}".encode("utf-8"), server_address)
            data, _ = client.recvfrom(BUFFER_SIZE)
            print(data.decode("utf-8", errors="replace"))
        except socket.timeout:
            print("[CLIENT] Server tidak merespons. Pastikan UDP server sudah berjalan dan IP/port benar.")
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
        print("\nKetik pesan biasa saja. Contoh: halo semuanya")
        print("Username sudah otomatis dikirim oleh program.")

        while True:
            try:
                message = input("> ").strip()

                if not message:
                    print("[CLIENT] Pesan tidak boleh kosong.")
                    continue

                if message == "/help":
                    print("Command: /list, /quit, /help, atau langsung ketik isi pesan.")
                    continue

                if message == "/list":
                    client.sendto(b"LIST", server_address)
                    continue

                if message == "/quit":
                    client.sendto(b"QUIT", server_address)
                    stop_event.set()
                    break

                # Client mengirim username otomatis, jadi user cukup mengetik isi pesan.
                client.sendto(f"MSG|{username}|{message}".encode("utf-8"), server_address)

            except KeyboardInterrupt:
                try:
                    client.sendto(b"QUIT", server_address)
                except OSError:
                    pass
                stop_event.set()
                print("\n[CLIENT] Keluar dari UDP chat.")
                break
            except OSError as error:
                print(f"[CLIENT] Error mengirim pesan: {error}")
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="UDP Broadcast Chat Client")
    parser.add_argument("--host", default=DEFAULT_HOST, help="IP server Ubuntu VirtualBox, default 192.168.18.99")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port server, default 5000")
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
