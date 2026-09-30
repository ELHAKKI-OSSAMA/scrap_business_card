"""Malware scanning integration point. ``MALWARE_SCANNER=clamav`` streams uploads to clamd
(INSTREAM protocol). With ``none`` the upload is still type-sniffed and fully decoded by
Pillow before acceptance, which rejects non-image payloads."""

from __future__ import annotations

import socket
import struct

from app.config import get_settings


class ScanResult:
    def __init__(self, clean: bool, signature: str | None = None, scanner: str = "none"):
        self.clean = clean
        self.signature = signature
        self.scanner = scanner


def scan_bytes(data: bytes) -> ScanResult:
    s = get_settings()
    if s.malware_scanner == "none":
        return ScanResult(True, scanner="none")
    with socket.create_connection((s.clamav_host, s.clamav_port), timeout=30) as sock:
        sock.sendall(b"zINSTREAM\0")
        for i in range(0, len(data), 65536):
            chunk = data[i : i + 65536]
            sock.sendall(struct.pack("!L", len(chunk)) + chunk)
        sock.sendall(struct.pack("!L", 0))
        reply = b""
        while not reply.endswith(b"\0"):
            part = sock.recv(4096)
            if not part:
                break
            reply += part
    text = reply.rstrip(b"\0").decode(errors="replace")
    if text.endswith("OK"):
        return ScanResult(True, scanner="clamav")
    return ScanResult(False, signature=text.split(":", 1)[-1].replace("FOUND", "").strip(), scanner="clamav")
