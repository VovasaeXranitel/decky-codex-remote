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

    def connect(self, host: str, port: str, token: str = "", proxy: dict[str, str] | None = None) -> None:
        self.connect_url(f"ws://{host}:{port}/", token, proxy)

    def connect_url(self, url: str, token: str = "", proxy: dict[str, str] | None = None) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"ws", "wss"}:
            raise ValueError("WebSocket endpoint must start with ws:// or wss://.")
        if not parsed.hostname:
            raise ValueError("WebSocket endpoint host is required.")
        host = parsed.hostname
        port_number = parsed.port or (443 if parsed.scheme == "wss" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        raw = self._open_socket(host, port_number, parsed.scheme == "wss", proxy)
        self._handshake(raw, host, port_number, path, token)
        raw.settimeout(1)
        self._sock = raw

    def _open_socket(self, host: str, port: int, use_tls: bool, proxy: dict[str, str] | None) -> SocketLike:
        if proxy and proxy.get("host") and proxy.get("port"):
            raw = socket.create_connection((proxy["host"], int(proxy["port"])), timeout=5)
            self._connect_proxy(raw, host, port)
        else:
            raw = socket.create_connection((host, port), timeout=5)
        if use_tls:
            context = ssl.create_default_context()
            return context.wrap_socket(raw, server_hostname=host)
        return raw

    def _connect_proxy(self, sock: socket.socket, host: str, port: int) -> None:
        request_head = (
            f"CONNECT {host}:{port} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Proxy-Connection: Keep-Alive\r\n\r\n"
        )
        sock.sendall(request_head.encode("ascii"))
        response = self._read_http_head(sock, "Proxy CONNECT failed.", "Proxy CONNECT response too large.")
        status_line = response.split(b"\r\n", 1)[0].decode("iso-8859-1")
        if " 200 " not in status_line:
            raise RuntimeError(f"Proxy CONNECT failed: {status_line}")

    def _handshake(self, raw: SocketLike, host: str, port_number: int, path: str, token: str) -> None:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}:{port_number}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
        ]
        if token:
            headers.append(f"Authorization: Bearer {token}")
        raw.sendall(("\r\n".join(headers) + "\r\n\r\n").encode("ascii"))
        response = self._read_http_head(raw, "WebSocket handshake failed.", "WebSocket handshake response too large.")
        head = response.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
        if " 101 " not in head.split("\r\n", 1)[0]:
            status_line = head.split("\r\n", 1)[0]
            if " 401 " in status_line or " 403 " in status_line:
                raise RuntimeError(f"{status_line}. Check the App Server token.")
            raise RuntimeError(status_line)
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
        if accept.lower() not in head.lower():
            raise RuntimeError("Invalid WebSocket accept header.")

    def _read_http_head(self, sock: SocketLike, closed_message: str, too_large_message: str) -> bytes:
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(1)
            if not chunk:
                raise RuntimeError(closed_message)
            response += chunk
            if len(response) > 65536:
                raise RuntimeError(too_large_message)
        return response

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
