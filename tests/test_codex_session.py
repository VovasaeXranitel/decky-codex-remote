import unittest
import threading
import time
from typing import Any

from codex_remote.application.codex_session import CodexSession


class StoredThreadSession(CodexSession):
    def __init__(self) -> None:
        super().__init__()
        self.resumed = False

    def _rpc(self, method: str, params: dict[str, Any] | None = None, timeout: float = 6) -> Any:
        if method == "thread/loaded/list":
            return {"data": []}
        if method == "thread/list":
            return {
                "data": [
                    {
                        "id": "thread-1",
                        "name": "Persisted chat",
                        "status": {"type": "notLoaded"},
                        "turns": [],
                    }
                ]
            }
        if method == "thread/resume":
            self.resumed = True
            return {"thread": {"id": "thread-1", "name": "Persisted chat"}}
        if method == "thread/read":
            if not self.resumed:
                raise RuntimeError("thread not found")
            return {
                "thread": {
                    "id": "thread-1",
                    "name": "Persisted chat",
                    "status": {"type": "idle"},
                    "turns": [],
                }
            }
        raise AssertionError(f"Unexpected RPC method: {method}")


class OfflineSession(CodexSession):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()

    def _run(self) -> None:
        self.started.set()
        self.release.wait(6)


class FailedConnectionSession(CodexSession):
    def __init__(self) -> None:
        super().__init__()
        self.reply_sent = False

    def connect(self) -> dict[str, Any]:
        return {"ok": False, "message": "Connection failed: offline"}

    def _send_reply(self, text: str) -> None:
        self.reply_sent = True


class InitializingSession(CodexSession):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[str] = []

    def _connect_socket(self) -> None:
        self.events.append("connect")

    def _rpc(self, method: str, params: dict[str, Any] | None = None, timeout: float = 6) -> Any:
        self.events.append(method)
        return {}

    def _send_json(self, message: dict[str, Any]) -> None:
        self.events.append(str(message.get("method") or "message"))

    def _refresh_snapshot(self, force: bool = False) -> None:
        self.events.append("refresh")

    def _receive_once(self, timeout: float = 1.0) -> None:
        self.events.append("receive")
        self._stop.set()


class BusyThreadSession(CodexSession):
    def __init__(self) -> None:
        super().__init__()
        self.resume_attempts: list[str] = []

    def _rpc(self, method: str, params: dict[str, Any] | None = None, timeout: float = 6) -> Any:
        params = params or {}
        if method == "thread/loaded/list":
            return {"data": []}
        if method == "thread/list":
            return {
                "data": [
                    {"id": "thread-busy", "name": "Desktop chat", "status": {"type": "notLoaded"}, "turns": []},
                    {"id": "thread-free", "name": "Deck chat", "status": {"type": "notLoaded"}, "turns": []},
                ]
            }
        if method == "thread/resume":
            thread_id = str(params.get("threadId"))
            self.resume_attempts.append(thread_id)
            if thread_id == "thread-busy":
                raise RuntimeError("thread already has an active writer")
            return {"thread": {"id": thread_id}}
        if method == "thread/read":
            return {
                "thread": {
                    "id": params.get("threadId"),
                    "name": "Deck chat",
                    "status": {"type": "idle"},
                    "turns": [],
                }
            }
        raise AssertionError(f"Unexpected RPC method: {method}")


class CodexSessionTest(unittest.TestCase):
    def test_state_starts_offline_connection_without_waiting(self) -> None:
        session = OfflineSession()
        session.configure({"host": "192.0.2.1", "port": "43871", "token": "test-token"})

        started_at = time.perf_counter()
        session.state()
        elapsed = time.perf_counter() - started_at
        session.release.set()

        self.assertTrue(session.started.wait(0.1))
        self.assertLess(elapsed, 0.25)

    def test_refresh_resumes_stored_thread_before_using_it(self) -> None:
        session = StoredThreadSession()
        session._connected = True

        session._refresh_snapshot(force=True)

        self.assertTrue(session.resumed)
        self.assertEqual(session._last_state["threadId"], "thread-1")
        self.assertEqual(session._last_state["thread"], "Persisted chat")
        self.assertTrue(session._last_state["threads"][0]["loaded"])

    def test_send_action_returns_disconnected_state_when_connect_fails(self) -> None:
        session = FailedConnectionSession()

        state = session.send_action("reply", "Continue")

        self.assertFalse(session.reply_sent)
        self.assertEqual(state["status"], "disconnected")
        self.assertEqual(state["transcript"][-1]["title"], "Connection")
        self.assertEqual(state["transcript"][-1]["status"], "failed")

    def test_run_acknowledges_initialize_before_other_requests(self) -> None:
        session = InitializingSession()

        session._run()

        self.assertEqual(session.events[:4], ["connect", "initialize", "initialized", "refresh"])

    def test_refresh_skips_thread_owned_by_another_writer(self) -> None:
        session = BusyThreadSession()
        session._connected = True

        session._refresh_snapshot(force=True)

        self.assertEqual(session.resume_attempts, ["thread-busy", "thread-free"])
        self.assertEqual(session._last_state["threadId"], "thread-free")
        self.assertEqual(session._last_state["thread"], "Deck chat")


if __name__ == "__main__":
    unittest.main()
