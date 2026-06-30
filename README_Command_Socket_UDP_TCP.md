# Daftar Command Program Socket UDP dan TCP

Dokumen ini berisi daftar command untuk menjalankan dan menggunakan program **Pemrograman Socket UDP dan TCP Advanced**.

Program terdiri dari dua bagian utama:

1. **UDP Chat**
2. **TCP Chat**

UDP digunakan untuk komunikasi pesan berbasis datagram, sedangkan TCP digunakan untuk komunikasi multi-client yang lebih stabil dan mendukung fitur login, private message, serta pengiriman file.

---

## 1. Struktur Folder Program

Struktur folder project:

```text
PJAR_Socket_UDP_TCP_Advanced/
│
├── udp/
│   ├── udp_server.py
│   └── udp_client.py
│
├── tcp/
│   ├── tcp_server.py
│   └── tcp_client.py
│
├── files/
│   └── pesan.txt
│
├── logs/
│
├── received_files/
│
└── README.md
```

Keterangan folder:

| Folder/File | Fungsi |
|---|---|
| `udp/udp_server.py` | Program server UDP |
| `udp/udp_client.py` | Program client UDP |
| `tcp/tcp_server.py` | Program server TCP |
| `tcp/tcp_client.py` | Program client TCP |
| `files/` | Folder contoh file yang dapat dikirim |
| `logs/` | Folder penyimpanan log pesan |
| `received_files/` | Folder penyimpanan file yang diterima server |

---

## 2. Persiapan Awal

Pastikan Python sudah terpasang di komputer.

Cek versi Python:

```bash
python --version
```

Masuk ke folder project:

```bash
cd PJAR_Socket_UDP_TCP_Advanced
```

> Catatan: Program ini menggunakan library bawaan Python, sehingga tidak perlu install package tambahan.

---

# A. Command UDP

## 3. Menjalankan UDP Server

Jalankan command berikut pada terminal pertama:

```bash
python udp/udp_server.py
```

Server UDP akan berjalan pada host dan port default.

---

## 4. Menjalankan UDP Client

Buka terminal baru, lalu jalankan:

```bash
python udp/udp_client.py
```

Client akan terhubung ke server UDP lokal menggunakan alamat:

```text
127.0.0.1
```

Alamat `127.0.0.1` digunakan agar program berjalan di komputer sendiri, bukan menggunakan IP VirtualBox.

---

## 5. Menjalankan UDP dengan Port Custom

Jika ingin menjalankan server UDP dengan port tertentu:

```bash
python udp/udp_server.py --port 5001
```

Kemudian jalankan client UDP dengan port yang sama:

```bash
python udp/udp_client.py --host 127.0.0.1 --port 5001
```

---

## 6. Menjalankan UDP ke Komputer Lain dalam Jaringan

Jika server dijalankan pada komputer lain, gunakan IP komputer server.

Contoh:

```bash
python udp/udp_client.py --host 192.168.1.10
```

> Ganti `192.168.1.10` dengan IP komputer yang menjalankan server.

---

## 7. Command di Dalam UDP Client

| Command | Fungsi |
|---|---|
| `/help` | Menampilkan bantuan command UDP |
| `/list` | Menampilkan daftar user UDP yang sedang aktif |
| `/quit` | Keluar dari UDP chat |
| `pesan biasa` | Mengirim pesan broadcast ke client lain |

Contoh penggunaan:

```text
/help
```

```text
/list
```

```text
halo semuanya
```

```text
/quit
```

---

## 8. Fitur UDP

Fitur yang tersedia pada program UDP:

1. Server dapat menerima pesan dari lebih dari satu client.
2. Pesan menggunakan format `username: pesan`.
3. Server dapat melakukan broadcast pesan ke client lain.
4. Tersedia validasi input agar pesan tidak kosong.
5. Tersedia command `/list` untuk melihat user aktif.
6. Tersedia logging pesan ke dalam folder `logs/`.
7. Tersedia error handling untuk menghindari program berhenti mendadak.

---

# B. Command TCP

## 9. Menjalankan TCP Server

Jalankan command berikut pada terminal pertama:

```bash
python tcp/tcp_server.py
```

Server TCP akan berjalan dan siap menerima koneksi dari beberapa client.

---

## 10. Menjalankan TCP Client

Buka terminal baru, lalu jalankan:

```bash
python tcp/tcp_client.py
```

Client akan terhubung ke server TCP lokal menggunakan alamat:

```text
127.0.0.1
```

---

## 11. Menjalankan TCP dengan Host dan Port Custom

Jika server TCP menggunakan port tertentu, jalankan client seperti berikut:

```bash
python tcp/tcp_client.py --host 127.0.0.1 --port 6000
```

---

## 12. Menjalankan TCP ke Komputer Lain dalam Jaringan

Jika server berada di komputer lain, gunakan IP komputer server.

Contoh:

```bash
python tcp/tcp_client.py --host 192.168.1.10
```

> Ganti `192.168.1.10` dengan IP komputer server yang sebenarnya.

---

## 13. Akun Login TCP

Program TCP menggunakan autentikasi sederhana.

| Username | Password |
|---|---|
| `admin` | `123` |
| `user1` | `123` |
| `user2` | `123` |

Contoh login:

```text
Username: admin
Password: 123
```

---

## 14. Command di Dalam TCP Client

| Command | Fungsi |
|---|---|
| `/help` | Menampilkan bantuan command TCP |
| `/list` | Menampilkan daftar user TCP yang sedang online |
| `/msg username pesan` | Mengirim private message ke user tertentu |
| `/sendfile path_file` | Mengirim file dari client ke server |
| `/quit` | Keluar dari TCP chat |
| `pesan biasa` | Mengirim chat broadcast ke semua user TCP |

Contoh penggunaan:

```text
/help
```

```text
/list
```

```text
halo semuanya
```

```text
/msg user1 halo ini pesan private
```

```text
/sendfile files/pesan.txt
```

```text
/quit
```

---

## 15. Fitur TCP

Fitur yang tersedia pada program TCP:

1. Server mampu menangani banyak client secara bersamaan.
2. Menggunakan multi-threading untuk setiap client.
3. Tersedia autentikasi sederhana menggunakan username dan password.
4. Mendukung chat real-time antar client.
5. Mendukung broadcast message.
6. Mendukung private message menggunakan command `/msg`.
7. Mendukung pengiriman file menggunakan command `/sendfile`.
8. Tersedia command `/list` untuk melihat user online.
9. Tersedia logging pesan dan aktivitas.
10. Tersedia error handling agar koneksi client tidak membuat server berhenti.

---

# C. Command Penting Saat Demo

## 16. Demo UDP

Terminal 1:

```bash
python udp/udp_server.py
```

Terminal 2:

```bash
python udp/udp_client.py
```

Terminal 3 untuk client kedua:

```bash
python udp/udp_client.py
```

Command yang dicoba di UDP client:

```text
/list
```

```text
halo dari client UDP
```

```text
/quit
```

---

## 17. Demo TCP

Terminal 1:

```bash
python tcp/tcp_server.py
```

Terminal 2:

```bash
python tcp/tcp_client.py
```

Terminal 3 untuk client kedua:

```bash
python tcp/tcp_client.py
```

Login client pertama:

```text
Username: admin
Password: 123
```

Login client kedua:

```text
Username: user1
Password: 123
```

Command yang dicoba di TCP client:

```text
/list
```

```text
halo dari client TCP
```

```text
/msg user1 halo ini pesan private
```

```text
/sendfile files/pesan.txt
```

```text
/quit
```

---

# D. Alur Kerja Program

## 18. Alur Kerja UDP

1. Server UDP dijalankan terlebih dahulu.
2. Client UDP dijalankan dan memasukkan username.
3. Client mengirim pesan ke server.
4. Server menerima pesan dari client.
5. Server menyimpan pesan ke file log.
6. Server melakukan broadcast pesan ke client lain.
7. Client dapat keluar menggunakan command `/quit`.

---

## 19. Alur Kerja TCP

1. Server TCP dijalankan terlebih dahulu.
2. Client TCP dijalankan dan melakukan koneksi ke server.
3. Client login menggunakan username dan password.
4. Jika login berhasil, client dapat menggunakan fitur chat.
5. Client dapat mengirim pesan broadcast.
6. Client dapat mengirim private message dengan command `/msg`.
7. Client dapat mengirim file dengan command `/sendfile`.
8. Server menyimpan file yang diterima ke folder `received_files/`.
9. Client dapat keluar menggunakan command `/quit`.

---

# E. Error Handling

Program sudah dilengkapi penanganan error seperti:

1. Pesan kosong tidak dikirim.
2. Username kosong tidak diterima.
3. Login TCP gagal jika username atau password salah.
4. Private message gagal jika user tujuan tidak ditemukan.
5. Pengiriman file gagal jika file tidak tersedia.
6. Koneksi client yang terputus tidak membuat server berhenti.
7. Port yang salah atau server belum aktif akan menampilkan pesan error.

---

# F. Catatan Penting

1. Jalankan server terlebih dahulu sebelum client.
2. Untuk demo lokal, gunakan host `127.0.0.1`.
3. Untuk demo antar laptop, gunakan IP komputer server.
4. Pastikan firewall tidak memblokir koneksi.
5. Gunakan beberapa terminal untuk menguji multiple client.
6. Screenshot yang disarankan:
   - UDP server berjalan
   - UDP client mengirim pesan
   - TCP server berjalan
   - TCP client login
   - TCP private message
   - TCP pengiriman file
   - Isi folder `logs/`
   - Isi folder `received_files/`

---

# G. Ringkasan Command

## UDP

```bash
python udp/udp_server.py
```

```bash
python udp/udp_client.py
```

```bash
python udp/udp_server.py --port 5001
```

```bash
python udp/udp_client.py --host 127.0.0.1 --port 5001
```

## TCP

```bash
python tcp/tcp_server.py
```

```bash
python tcp/tcp_client.py
```

```bash
python tcp/tcp_client.py --host 127.0.0.1 --port 6000
```

## Command UDP Client

```text
/help
/list
/quit
pesan biasa
```

## Command TCP Client

```text
/help
/list
/msg username pesan
/sendfile path_file
/quit
pesan biasa
```
