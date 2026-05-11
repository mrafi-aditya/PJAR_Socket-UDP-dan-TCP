# PJAR Socket Programming UDP dan TCP

Project ini merupakan implementasi pemrograman socket menggunakan bahasa Python dengan menggunakan dua protokol komunikasi jaringan, yaitu UDP (User Datagram Protocol) dan TCP (Transmission Control Protocol).

Program dibuat untuk memenuhi tugas mata kuliah Pemrograman Jaringan dengan menerapkan konsep client-server, komunikasi data antar perangkat, multi-client connection, autentikasi sederhana, command system, logging, dan pengiriman file.

Implementasi dilakukan menggunakan Python Socket Programming dan dijalankan pada lingkungan lokal serta VirtualBox sebagai server.

---

# Tujuan Project

Tujuan dari project ini adalah:

- Memahami konsep dasar socket programming.
- Memahami perbedaan protokol UDP dan TCP.
- Mengimplementasikan komunikasi client-server.
- Mengimplementasikan multi-client connection.
- Mengimplementasikan pengiriman pesan dan file melalui jaringan.
- Mengimplementasikan autentikasi sederhana pada TCP.
- Memahami penerapan threading pada server multi-client.

---

# Perbedaan UDP dan TCP

## UDP (User Datagram Protocol)

UDP merupakan protokol komunikasi yang bersifat:

- Connectionless
- Tidak menjamin data diterima
- Transfer data lebih cepat
- Tidak memiliki validasi koneksi

Pada project ini, UDP digunakan untuk implementasi chat broadcast sederhana.

---

## TCP (Transmission Control Protocol)

TCP merupakan protokol komunikasi yang bersifat:

- Connection-oriented
- Menjamin data diterima
- Lebih stabil dibanding UDP
- Mendukung komunikasi real-time multi-client

Pada project ini, TCP digunakan untuk implementasi chat multi-client dengan autentikasi dan pengiriman file.

---

# Struktur Project

```text
PJAR_Socket-UDP-dan-TCP/
├── files/
│   └── pesan.txt
├── received_files/
├── tcp/
│   ├── tcp_client.py
│   └── tcp_server.py
├── udp/
│   ├── udp_client.py
│   └── udp_server.py
├── udp_chat.log
└── README.md
```

---

# Penjelasan Struktur Folder

## Folder `udp/`

Berisi program socket berbasis UDP:

- `udp_server.py`
  Program server UDP.

- `udp_client.py`
  Program client UDP.

---

## Folder `tcp/`

Berisi program socket berbasis TCP:

- `tcp_server.py`
  Program server TCP multi-client.

- `tcp_client.py`
  Program client TCP.

---

## Folder `files/`

Berisi file contoh yang digunakan untuk pengujian fitur pengiriman file.

Contoh:

```text
pesan.txt
```

---

## Folder `received_files/`

Folder yang digunakan server TCP untuk menyimpan file yang diterima dari client.

---

# Teknologi yang Digunakan

Project ini menggunakan:

- Python 3
- Socket Library
- Threading
- File Handling
- CLI (Command Line Interface)

---

# Implementasi UDP

## Fitur UDP

Fitur yang tersedia pada implementasi UDP:

- Server dan client UDP
- Multi-client communication
- Broadcast pesan ke seluruh client
- Format pesan:
  
```text
username: pesan
```

- Validasi input kosong
- Logging pesan ke file
- Penanganan error sederhana

---

## Cara Kerja UDP

1. Client memasukkan username.
2. Client mengirim pesan ke server.
3. Server menerima pesan.
4. Server menyimpan pesan ke file log.
5. Server melakukan broadcast pesan ke client lain.
6. Semua client menerima pesan secara real-time.

---

## Logging UDP

Semua pesan UDP akan disimpan pada file:

```text
udp_chat.log
```

Contoh isi log:

```text
2024-01-01 10:20:00 - admin: Halo semua
```

---

# Implementasi TCP

## Fitur TCP

Fitur yang tersedia pada implementasi TCP:

- Server dan client TCP
- Multi-client menggunakan threading
- Login username dan password
- Chat real-time
- Command-based system
- Pengiriman file sederhana
- Penanganan disconnect client
- Penanganan error sederhana

---

## Cara Kerja TCP

1. Client melakukan koneksi ke server.
2. Client melakukan login menggunakan username dan password.
3. Server memvalidasi login.
4. Client dapat mengirim pesan ke client lain.
5. Client dapat menggunakan command tertentu.
6. Client dapat mengirim file ke server.
7. Server menyimpan file pada folder `received_files`.

---

# Command TCP

| Command | Fungsi |
|---|---|
| `/list` | Menampilkan user online |
| `/sendfile path_file` | Mengirim file ke server |
| `/quit` | Keluar dari chat |

---

# Akun Login TCP

| Username | Password |
|---|---|
| admin | 123 |
| user1 | 123 |
| user2 | 123 |

---

# Cara Menjalankan Program

## Clone Repository

```bash
git clone https://github.com/username/PJAR_Socket-UDP-dan-TCP.git
```

Masuk ke folder project:

```bash
cd PJAR_Socket-UDP-dan-TCP
```

---

# Menjalankan UDP

## Menjalankan UDP Server

```bash
python3 udp/udp_server.py
```

## Menjalankan UDP Client

```bash
python3 udp/udp_client.py
```

---

# Menjalankan TCP

## Menjalankan TCP Server

```bash
python3 tcp/tcp_server.py
```

## Menjalankan TCP Client

```bash
python3 tcp/tcp_client.py
```

---

# Konfigurasi IP Server

Pada file client UDP dan TCP, ubah IP server sesuai IP VirtualBox/server.

Contoh:

```python
SERVER_IP = "192.168.56.101"
```

---

# Cara Melihat IP Server

## Linux / VirtualBox

```bash
ip a
```

## Windows

```bash
ipconfig
```

---

# Contoh Penggunaan UDP

## Login Username

```text
Masukkan username: admin
```

## Mengirim Pesan

```text
Halo semuanya
```

Output pada client lain:

```text
admin: Halo semuanya
```

---

# Contoh Penggunaan TCP

## Login

```text
Username:
admin

Password:
123
```

---

## Chat Real-time

```text
Halo semuanya
```

Pesan akan diterima oleh client lain secara real-time.

---

## Melihat User Online

```text
/list
```

Output:

```text
User online: admin, user1
```

---

## Mengirim File

```text
/sendfile ../files/pesan.txt
```

---

# Contoh Isi File

File `files/pesan.txt`

```text
ini pesan dari muhammad rafi aditya
```

---

# Penyimpanan File

File yang berhasil dikirim client akan otomatis disimpan server pada folder:

```text
received_files/
```

---

# Penanganan Error

Program memiliki beberapa error handling sederhana, seperti:

- Validasi login
- Validasi pesan kosong
- Validasi format pesan
- Validasi file tidak ditemukan
- Penanganan disconnect client
- Penanganan port yang sedang digunakan
- Penanganan client yang terputus

---

# Kelebihan Program

- Mendukung multi-client
- Implementasi UDP dan TCP sekaligus
- Memiliki sistem login sederhana
- Mendukung broadcast chat
- Mendukung pengiriman file
- Struktur kode modular
- Mudah dijalankan pada Linux maupun Windows

---

# Screenshot Program

Tambahkan screenshot berikut:

1. UDP Server Running
2. UDP Multi Client Chat
3. TCP Login Berhasil
4. TCP Multi Client Chat
5. TCP Command `/list`
6. TCP Pengiriman File
7. Isi folder `received_files`
8. Isi file `udp_chat.log`

---

# Kesimpulan

Project ini berhasil mengimplementasikan socket programming menggunakan protokol UDP dan TCP dengan fitur multi-client communication, autentikasi sederhana, pengiriman file, logging, dan command system.

Melalui project ini dapat dipahami bahwa:

- UDP lebih cepat namun tidak menjamin pengiriman data.
- TCP lebih stabil dan cocok untuk komunikasi real-time multi-client.
- Socket programming dapat digunakan untuk membangun sistem komunikasi jaringan sederhana.

---

# Author

Muhammad Rafi Aditya