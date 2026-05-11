# udp/udp_client.py
import socket
import threading

SERVER_IP = "192.168.18.99"  # ganti dengan IP VirtualBox server
SERVER_PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

username = input("Masukkan username: ").strip()

def receive_message():
    while True:
        try:
            data, _ = client.recvfrom(1024)
            print(f"\n{data.decode()}")
        except:
            break

threading.Thread(target=receive_message, daemon=True).start()

print("Ketik pesan. Format otomatis: username: pesan")
print("Ketik /quit untuk keluar.")

while True:
    message = input("> ").strip()

    if message == "/quit":
        break

    if not message:
        print("Pesan tidak boleh kosong.")
        continue

    full_message = f"{username}: {message}"
    client.sendto(full_message.encode(), (SERVER_IP, SERVER_PORT))

client.close()