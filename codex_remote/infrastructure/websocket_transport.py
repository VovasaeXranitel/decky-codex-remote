import base64
import hashlib
import json
import os
import socket
import ssl
import struct
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse


SocketLike = socket.socket | ssl.SSLSocket


class WebSocketTransport:
    def __init__(
        self,
        sock: SocketLike | None = None,
        mask_provider: Callable[[], bytes] | None = None,
    ) -> None:
        self._sock = sock
        self._mask_provider = mask_provider or (lambda: os.urandom(4))

    @property
    def sock(self) -> SocketLike | None:
        return self._sock

    def connect(self, host: str, port: str, token: str = "") -> None:
        port_number = int(port)
        raw = socket.create_connection((host, port_number), timeout=5)
        parsed = urlparse(f"ws://{host}:{port_number}/")
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            f"GET {parsed.path or '/'} HTTP/1.1",
            f"Host: {host}:{port_number}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
        ]
        if token:
            headers.append(f"Authorization: Bearer {token}")
        raw.sendall(("\r\n".join(headers) + "\r\n\r\n").encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = raw.recv(4096)
            if not chunk:
                raise RuntimeError("WebSocket handshake failed.")
            response += chunk
            if len(response) > 65536:
                raise RuntimeError("WebSocket handshake response too large.")
        head = response.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
        if " 101 " not in head.split("\r\n", 1)[0]:
            status_line = head.split("\r\n", 1)[0]
            if " 401 " in status_line or " 403 " in status_line:
                raise RuntimeError(f"{status_line}. Check the App Server token.")
            raise RuntimeError(status_line)
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
        if accept.lower() not in head.lower():
            raise RuntimeError("Invalid WebSocket accept header.")
        raw.settimeout(1)
        self._sock = raw

    def close(self) -> None:
        sock = self._sock
        self._sock = None
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    def send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_frame(0x1, data)

    def receive_json(self, timeout: float = 1.0) -> tuple[int, dict[str, Any] | None]:
        opcode, payload = self.receive_frame(timeout)
        if opcode != 0x1:
            return opcode, None
        return opcode, json.loads(payload.decode("utf-8"))

    def receive_frame(self, timeout: float = 1.0) -> tuple[int, bytes]:
        sock = self._require_socket()
        previous_timeout = sock.gettimeout()
        sock.settimeout(timeout)
        try:
            opcode, payload = self.read_frame()
        finally:
            sock.settimeout(previous_timeout)
        return opcode, payload

    def send_frame(self, opcode: int, payload: bytes) -> None:
        sock = self._require_socket()
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = self._mask_provider()
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        sock.sendall(bytes(header) + masked)

    def read_frame(self) -> tuple[int, bytes]:
        sock = self._require_socket()
        first = self._read_exact(sock, 2)
        opcode = first[0] & 0x0F
        masked = bool(first[1] & 0x80)
        length = first[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(sock, 8))[0]
        mask = self._read_exact(sock, 4) if masked else b""
        payload = self._read_exact(sock, length) if length else b""
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def _require_socket(self) -> SocketLike:
        if not self._sock:
            raise RuntimeError("Socket is not connected.")
        return self._sock

    def _read_exact(self, sock: SocketLike, count: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < count:
            chunk = sock.recv(count - len(chunks))
            if not chunk:
                raise RuntimeError("Socket closed.")
            chunks.extend(chunk)
        return bytes(chunks)
