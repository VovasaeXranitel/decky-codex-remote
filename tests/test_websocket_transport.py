import io
import unittest

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


if __name__ == "__main__":
    unittest.main()
