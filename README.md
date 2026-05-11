# PJAR_Socket-UDP-dan-TCP

# Pemrograman Socket UDP dan TCP

Project ini berisi implementasi socket programming menggunakan Python.

## Fitur UDP

- Server dan client UDP
- Server menerima pesan dari banyak client
- Format pesan: username: pesan
- Validasi input kosong
- Logging pesan ke file udp_chat.log
- Broadcast pesan ke client lain

## Fitur TCP

- Server dan client TCP
- Multi-client menggunakan threading
- Autentikasi username dan password
- Chat real-time
- Command-based system:
  - /list untuk melihat user online
  - /sendfile untuk mengirim file
  - /quit untuk keluar
- Pengiriman file ke server

## Akun Login TCP

| Username | Password |
|---|---|
| admin | 123 |
| user1 | 123 |
| user2 | 123 |

## Cara Menjalankan

### UDP Server

```bash
python udp/udp_server.py