"""Helper protokol TCP berbasis JSON per baris.

Setiap pesan dikirim sebagai satu JSON object diakhiri newline.
Cara ini membuat chat dan file transfer lebih rapi dibanding menggabungkan teks mentah.
"""

from __future__ import annotations

import json
import socket
from typing import Any


def send_json(sock: socket.socket, payload: dict[str, Any]) -> None:
    """Mengirim satu pesan JSON ke socket."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"
    sock.sendall(data)


def read_json_line(reader) -> dict[str, Any] | None:
    """Membaca satu baris JSON dari file-like socket reader."""
    line = reader.readline()
    if not line:
        return None
    return json.loads(line)
