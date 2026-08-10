import io
import unittest
from unittest.mock import patch

from codex_remote.infrastructure.websocket_transport import WebSocketTransport


class FakeSocket:
    def __init__(self, data: bytes = b"") -> None:
        self._data = io.BytesIO(data)
        self.sent = bytearray()
        self.timeout: float | None = None

    def recv(self, count: int) -> bytes:
        return self._data.read(count)

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def settimeout(self, timeout: float | None) -> None:
        self.timeout = timeout

    def gettimeout(self) -> float | None:
        return self.timeout

    def close(self) -> None:
        pass


class WebSocketTransportTest(unittest.TestCase):
    def test_send_frame_masks_client_payload(self) -> None:
        sock = FakeSocket()
        transport = WebSocketTransport(sock=sock, mask_provider=lambda: b"\x01\x02\x03\x04")

        transport.send_frame(0x1, b"test")

        self.assertEqual(sock.sent[:2], bytes([0x81, 0x80 | 4]))
        self.assertEqual(sock.sent[2:6], b"\x01\x02\x03\x04")
        self.assertEqual(bytes(sock.sent[6:]), bytes([ord("t") ^ 1, ord("e") ^ 2, ord("s") ^ 3, ord("t") ^ 4]))

    def test_read_frame_decodes_unmasked_server_payload(self) -> None:
        sock = FakeSocket(bytes([0x81, 0x05]) + b"hello")
        transport = WebSocketTransport(sock=sock)

        opcode, payload = transport.read_frame()

        self.assertEqual(opcode, 0x1)
        self.assertEqual(payload, b"hello")

    def test_read_frame_decodes_masked_payload(self) -> None:
        mask = b"\x01\x02\x03\x04"
        payload = b"pong"
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        sock = FakeSocket(bytes([0x89, 0x80 | len(payload)]) + mask + masked)
        transport = WebSocketTransport(sock=sock)

        opcode, decoded = transport.read_frame()

        self.assertEqual(opcode, 0x9)
        self.assertEqual(decoded, payload)

    def test_connect_url_can_tunnel_websocket_through_http_proxy(self) -> None:
        key = "AQIDBAUGBwgJCgsMDQ4PEA=="
        accept = "C/0nmHhBztSRGR1CwL6Tf4ZjwpY="
        proxy_response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
        websocket_response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode("ascii")
        sock = FakeSocket(proxy_response + websocket_response)
        transport = WebSocketTransport()

        with patch("socket.create_connection", return_value=sock) as create_connection, patch("os.urandom", return_value=b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"):
            transport.connect_url(
                "ws://codex.example:43871/socket",
                "secret-token",
                proxy={"host": "127.0.0.1", "port": "12334"},
            )

        create_connection.assert_called_once_with(("127.0.0.1", 12334), timeout=5)
        sent = bytes(sock.sent).decode("iso-8859-1")
        self.assertIn("CONNECT codex.example:43871 HTTP/1.1\r\n", sent)
        self.assertIn("GET /socket HTTP/1.1\r\n", sent)
        self.assertIn("Host: codex.example:43871\r\n", sent)
        self.assertIn("Authorization: Bearer secret-token\r\n", sent)

    def test_connect_url_preserves_frame_bytes_after_handshake(self) -> None:
        key = "AQIDBAUGBwgJCgsMDQ4PEA=="
        accept = "C/0nmHhBztSRGR1CwL6Tf4ZjwpY="
        websocket_response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode("ascii")
        sock = FakeSocket(websocket_response + bytes([0x81, 0x02]) + b"{}")
        transport = WebSocketTransport()

        with patch("socket.create_connection", return_value=sock), patch("os.urandom", return_value=b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"):
            transport.connect_url("ws://codex.example:43871/socket")

        opcode, payload = transport.read_frame()

        self.assertEqual(opcode, 0x1)
        self.assertEqual(payload, b"{}")


if __name__ == "__main__":
    unittest.main()
