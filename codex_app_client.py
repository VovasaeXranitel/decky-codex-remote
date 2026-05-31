import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import threading
import time
from typing import Any
from urllib.parse import urlparse


class CodexAppClient:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._connected = False
        self._error = "Not connected."
        self._settings: dict[str, Any] = {}
        self._sock: socket.socket | ssl.SSLSocket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._next_id = 1
        self._pending: dict[int, dict[str, Any]] = {}
        self._pending_approval: dict[str, Any] | None = None
        self._active_thread_id: str | None = None
        self._active_turn_id: str | None = None
        self._threads: list[dict[str, Any]] = []
        self._messages: list[str] = []
        self._live_items: list[dict[str, Any]] = []
        self._stream_item: dict[str, Any] | None = None
        self._last_state: dict[str, Any] = {
            "status": "disconnected",
            "thread": "Decky remote",
            "threadId": "",
            "threads": [],
            "task": "Configure Codex App Server connection",
            "transcript": [
                {
                    "id": "setup",
                    "kind": "system",
                    "title": "Setup",
                    "body": "Enter your Codex App Server host, port, and token.",
                    "status": "",
                }
            ],
            "messages": ["Enter your Codex App Server host, port, and token."],
        }

    def configure(self, settings: dict[str, Any]) -> None:
        normalized = {
            "host": str(settings.get("host") or "").strip(),
            "port": str(settings.get("port") or "43871").strip(),
            "token": str(settings.get("token") or "").strip(),
            "autoRefresh": bool(settings.get("autoRefresh", True)),
        }

        with self._lock:
            if normalized == self._settings and self._thread and self._thread.is_alive():
                return
            self.disconnect()
            self._settings = normalized
            self._error = "Not connected."

    def connect(self) -> dict[str, Any]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return {"ok": self._connected, "message": self._error if not self._connected else "Connected."}

            if not self._settings.get("host"):
                self._error = "Host is not configured."
                return {"ok": False, "message": self._error}

            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="CodexAppClient", daemon=True)
            self._thread.start()

        deadline = time.time() + 4
        while time.time() < deadline:
            with self._lock:
                if self._connected:
                    return {"ok": True, "message": "Connected."}
                if self._error and self._error != "Not connected.":
                    return {"ok": False, "message": self._error}
            time.sleep(0.05)

        return {"ok": False, "message": "Connection timed out."}

    def disconnect(self) -> None:
        self._stop.set()
        sock = self._sock
        self._sock = None
        if sock:
            try:
                sock.close()
            except OSError:
                pass
        self._connected = False

    def state(self) -> dict[str, Any]:
        self.connect()
        with self._lock:
            state = dict(self._last_state)
            if self._pending_approval:
                state["status"] = "approval"
                state["approvalText"] = self._pending_approval.get("text") or "Approval needed"
                command = self._pending_approval.get("command")
                if command:
                    state["command"] = command
            return state

    def send_action(self, action: str, payload: str | None = None) -> dict[str, Any]:
        self.connect()
        if action == "approve":
            self._answer_approval(True)
        elif action == "deny":
            self._answer_approval(False)
        elif action == "pause":
            self._interrupt()
        elif action == "reply" and payload and payload.strip():
            self._send_reply(payload.strip())
        else:
            self._add_message(f"Ignored action: {action}")
        self._refresh_snapshot()
        return self.state()

    def select_thread(self, thread_id: str) -> dict[str, Any]:
        self.connect()
        selected_id = str(thread_id or "").strip()
        if not selected_id:
            self._add_message("No chat selected.")
            return self.state()
        with self._lock:
            self._active_thread_id = selected_id
            self._active_turn_id = None
            self._pending_approval = None
        self._refresh_snapshot()
        return self.state()

    def account(self) -> dict[str, Any]:
        result = self.connect()
        if not result["ok"]:
            return {"ok": False, "message": result["message"], "account": None, "requiresOpenaiAuth": True}
        try:
            account = self._rpc("account/read", {"refreshToken": False}, timeout=8)
            return {"ok": True, "message": self._account_message(account), **account}
        except Exception as exc:
            return {"ok": False, "message": f"Account read failed: {exc}", "account": None, "requiresOpenaiAuth": True}

    def start_chatgpt_login(self) -> dict[str, Any]:
        result = self.connect()
        if not result["ok"]:
            return {"ok": False, "message": result["message"]}
        try:
            login = self._rpc("account/login/start", {"type": "chatgptDeviceCode"}, timeout=10)
            self._add_message("ChatGPT device login started.")
            return {"ok": True, "message": "Enter this code in ChatGPT.", **login}
        except Exception as exc:
            return {"ok": False, "message": f"ChatGPT login failed: {exc}"}

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._connect_socket()
                self._connected = True
                self._error = ""
                self._rpc("initialize", {
                    "clientInfo": {
                        "name": "codex-remote-decky",
                        "title": "Codex Remote",
                        "version": "0.1.0",
                    },
                    "capabilities": {"experimentalApi": True},
                }, timeout=8)
                self._refresh_snapshot()
                while not self._stop.is_set():
                    try:
                        self._receive_once(timeout=1.0)
                    except socket.timeout:
                        continue
            except Exception as exc:
                with self._lock:
                    self._connected = False
                    self._error = f"Connection failed: {exc}"
                    self._last_state = {
                        "status": "disconnected",
                        "thread": "Decky remote",
                        "threadId": "",
                        "threads": [],
                        "task": "Codex App Server is not reachable",
                        "transcript": [
                            {
                                "id": "connection-error",
                                "kind": "error",
                                "title": "Connection",
                                "body": self._error,
                                "status": "failed",
                            }
                        ],
                        "messages": [self._error],
                    }
                self.disconnect()
                if not self._stop.is_set():
                    time.sleep(2)

    def _connect_socket(self) -> None:
        host = self._settings["host"]
        port = int(self._settings["port"])
        token = self._settings.get("token") or ""
        raw = socket.create_connection((host, port), timeout=5)
        parsed = urlparse(f"ws://{host}:{port}/")
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        headers = [
            f"GET {parsed.path or '/'} HTTP/1.1",
            f"Host: {host}:{port}",
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
            raise RuntimeError(head.split("\r\n", 1)[0])
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
        if accept.lower() not in head.lower():
            raise RuntimeError("Invalid WebSocket accept header.")
        raw.settimeout(1)
        self._sock = raw

    def _rpc(self, method: str, params: dict[str, Any] | None = None, timeout: float = 6) -> Any:
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            event = threading.Event()
            self._pending[request_id] = {"event": event}
        self._send_json({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})

        deadline = time.time() + timeout
        if threading.current_thread() is self._thread:
            while not event.is_set() and time.time() < deadline:
                try:
                    self._receive_once(timeout=min(0.2, max(0.01, deadline - time.time())))
                except socket.timeout:
                    pass
        else:
            event.wait(timeout)

        if not event.is_set():
            with self._lock:
                self._pending.pop(request_id, None)
            raise TimeoutError(f"{method} timed out")
        with self._lock:
            result = self._pending.pop(request_id)
        if "error" in result:
            raise RuntimeError(result["error"])
        return result.get("result")

    def _receive_once(self, timeout: float = 1.0) -> None:
        sock = self._sock
        if not sock:
            raise RuntimeError("Socket is not connected.")
        previous_timeout = sock.gettimeout()
        sock.settimeout(timeout)
        try:
            opcode, payload = self._read_frame(sock)
        finally:
            sock.settimeout(previous_timeout)
        if opcode == 0x8:
            raise RuntimeError("WebSocket closed by server.")
        if opcode == 0x9:
            self._send_frame(0xA, payload)
            return
        if opcode != 0x1:
            return
        self._handle_message(json.loads(payload.decode("utf-8")))

    def _handle_message(self, message: dict[str, Any]) -> None:
        if "id" in message and ("result" in message or "error" in message):
            with self._lock:
                pending = self._pending.get(message["id"])
                if pending:
                    if "error" in message:
                        pending["error"] = message["error"]
                    else:
                        pending["result"] = message.get("result")
                    pending["event"].set()
            return

        method = message.get("method")
        params = message.get("params") or {}
        if "id" in message and method:
            if method in {
                "item/commandExecution/requestApproval",
                "item/fileChange/requestApproval",
                "item/permissions/requestApproval",
                "execCommandApproval",
                "applyPatchApproval",
            }:
                self._store_approval(message["id"], method, params)
            elif method == "account/chatgptAuthTokens/refresh":
                self._send_json({"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32001, "message": "Please refresh auth in Codex App on PC."}})
            else:
                self._send_json({"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": f"Unsupported request: {method}"}})
            return

        if method:
            self._handle_notification(method, params)

    def _handle_notification(self, method: str, params: dict[str, Any]) -> None:
        if method == "thread/status/changed":
            self._active_thread_id = params.get("threadId") or self._active_thread_id
            self._refresh_snapshot()
        elif method == "turn/started":
            self._active_thread_id = params.get("threadId") or self._active_thread_id
            turn = params.get("turn") or {}
            self._active_turn_id = turn.get("id") or params.get("turnId") or self._active_turn_id
            self._add_event("event", "Turn started", "Codex started working.", "running")
        elif method == "turn/completed":
            self._active_turn_id = None
            self._pending_approval = None
            self._finish_stream_item()
            self._add_event("event", "Turn completed", "Codex finished the turn.", "completed")
            self._refresh_snapshot()
        elif method in {"agent/message/delta", "reasoning/summary/text/delta", "reasoning/text/delta"}:
            text = params.get("delta") or params.get("text")
            if text:
                kind = "reasoning" if "reasoning" in method else "assistant"
                self._append_stream_delta(kind, str(text))
        elif method == "error":
            self._add_event("error", "Codex error", params.get("message") or "Codex App Server error.", "failed")
        elif method == "account/login/completed":
            if params.get("success"):
                self._add_event("event", "ChatGPT", "Login completed.", "completed")
            else:
                self._add_event("error", "ChatGPT", f"Login failed: {params.get('error') or 'unknown error'}", "failed")
        elif method == "account/updated":
            mode = params.get("authMode") or "signed out"
            plan = params.get("planType")
            self._add_event("event", "Account", f"{mode}{f' ({plan})' if plan else ''}", "completed")

    def _refresh_snapshot(self) -> None:
        if not self._connected:
            return
        try:
            loaded = self._rpc("thread/loaded/list", {"limit": 10}, timeout=4)
            loaded_ids = loaded.get("data") or []
            listed = self._rpc("thread/list", {"limit": 8, "archived": False, "sortKey": "updated_at", "sortDirection": "desc"}, timeout=5)
            threads = listed.get("data") or []
            summaries = self._thread_summaries(threads, loaded_ids)
            thread_id = self._active_thread_id or (loaded_ids[0] if loaded_ids else None)
            if not thread_id and threads:
                thread_id = threads[0].get("id")
            if not thread_id:
                self._last_state = {
                    "status": "idle",
                    "thread": "No threads",
                    "threadId": "",
                    "threads": [],
                    "task": "Connected to Codex App Server",
                    "transcript": [
                        {
                            "id": "no-threads",
                            "kind": "system",
                            "title": "No chats",
                            "body": "No Codex threads were found.",
                            "status": "",
                        }
                    ],
                    "messages": ["No Codex threads were found."],
                }
                return
            self._active_thread_id = thread_id
            data = self._rpc("thread/read", {"threadId": thread_id, "includeTurns": True}, timeout=5)
            thread = data.get("thread") or {}
            title = self._thread_title(thread)
            status = self._status_from_thread(thread)
            self._active_turn_id = self._active_turn_id or self._find_active_turn_id(thread)
            transcript = self._transcript_from_thread(thread)
            messages = [item.get("body", "") for item in transcript if item.get("body")]
            if self._messages:
                messages = (messages + self._messages)[-5:]
            if self._live_items:
                transcript = (transcript + self._live_items)[-80:]
            if self._stream_item:
                transcript = (transcript + [self._stream_item])[-80:]
            if thread_id and not any(item["id"] == thread_id for item in summaries):
                summaries.insert(0, self._thread_summary(thread, loaded_ids))
            summaries = [
                {**item, "active": item["id"] == thread_id}
                for item in summaries
            ]
            with self._lock:
                self._threads = summaries
            self._last_state = {
                "status": status,
                "thread": str(title)[:60],
                "threadId": thread_id,
                "threads": summaries,
                "task": self._task_from_thread(thread, status),
                "transcript": transcript[-80:] or [
                    {
                        "id": "connected",
                        "kind": "system",
                        "title": "Connected",
                        "body": "Connected to Codex App Server.",
                        "status": "completed",
                    }
                ],
                "messages": messages[-5:] or ["Connected to Codex App Server."],
            }
        except Exception as exc:
            self._add_message(f"Refresh failed: {exc}")

    def _thread_summaries(self, threads: list[dict[str, Any]], loaded_ids: list[str]) -> list[dict[str, Any]]:
        summaries = [self._thread_summary(thread, loaded_ids) for thread in threads if thread.get("id")]
        loaded_missing = [thread_id for thread_id in loaded_ids if thread_id and not any(item["id"] == thread_id for item in summaries)]
        for thread_id in loaded_missing:
            try:
                data = self._rpc("thread/read", {"threadId": thread_id, "includeTurns": False}, timeout=3)
                thread = data.get("thread") or {"id": thread_id}
            except Exception:
                thread = {"id": thread_id, "preview": "Loaded Codex chat"}
            summaries.insert(0, self._thread_summary(thread, loaded_ids))
        return summaries[:8]

    def _thread_summary(self, thread: dict[str, Any], loaded_ids: list[str]) -> dict[str, Any]:
        thread_id = str(thread.get("id") or "")
        status = self._status_from_thread(thread)
        return {
            "id": thread_id,
            "title": self._thread_title(thread),
            "status": status,
            "active": thread_id == self._active_thread_id,
            "loaded": thread_id in loaded_ids,
            "updatedAt": thread.get("updatedAt") or 0,
        }

    def _thread_title(self, thread: dict[str, Any]) -> str:
        for key in ("name", "preview"):
            value = thread.get(key)
            if isinstance(value, str) and value.strip():
                return self._clean_thread_title(value)
        cwd = thread.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            return os.path.basename(cwd.rstrip("/")) or cwd
        thread_id = str(thread.get("id") or "")
        if thread_id:
            return f"Codex chat {thread_id[:6]}"
        return "Untitled chat"

    def _clean_thread_title(self, value: str) -> str:
        collapsed = " ".join(value.strip().split())
        if len(collapsed) > 72:
            return f"{collapsed[:69]}..."
        return collapsed

    def _store_approval(self, request_id: int | str, method: str, params: dict[str, Any]) -> None:
        command = params.get("command") or params.get("reason")
        if not command and params.get("fileChanges"):
            command = "Apply proposed file changes"
        text = "Approval needed"
        if "commandExecution" in method or method == "execCommandApproval":
            text = "Run command?"
        elif "fileChange" in method or method == "applyPatchApproval":
            text = "Apply file changes?"
        elif "permissions" in method:
            text = "Grant permissions?"
        with self._lock:
            self._pending_approval = {
                "rpc_id": request_id,
                "method": method,
                "params": params,
                "text": text,
                "command": command,
            }
        self._add_event("approval", text, str(command or "Approval needed"), "pending")

    def _answer_approval(self, approved: bool) -> None:
        with self._lock:
            approval = self._pending_approval
            self._pending_approval = None
        if not approval:
            self._add_event("event", "Approval", "No approval is pending.", "")
            return
        method = approval["method"]
        if method in {"item/commandExecution/requestApproval", "item/fileChange/requestApproval", "item/permissions/requestApproval"}:
            decision = "accept" if approved else "decline"
        elif method in {"execCommandApproval", "applyPatchApproval"}:
            decision = "approved" if approved else "denied"
        else:
            decision = "accept" if approved else "decline"
        self._send_json({"jsonrpc": "2.0", "id": approval["rpc_id"], "result": {"decision": decision}})
        self._add_event("approval", "Approval answered", "Approved from Steam Deck." if approved else "Denied from Steam Deck.", "completed" if approved else "denied")

    def _send_reply(self, text: str) -> None:
        if not self._active_thread_id:
            self._refresh_snapshot()
        if not self._active_thread_id:
            raise RuntimeError("No active Codex thread.")
        input_items = [{"type": "text", "text": text}]
        if self._active_turn_id:
            self._rpc("turn/steer", {"threadId": self._active_thread_id, "expectedTurnId": self._active_turn_id, "input": input_items}, timeout=8)
        else:
            result = self._rpc("turn/start", {"threadId": self._active_thread_id, "input": input_items}, timeout=8)
            turn = (result or {}).get("turn") or {}
            self._active_turn_id = turn.get("id") or (result or {}).get("turnId")
        self._add_event("user", "You", text, "sent")

    def _interrupt(self) -> None:
        if self._active_thread_id and self._active_turn_id:
            self._rpc("turn/interrupt", {"threadId": self._active_thread_id, "turnId": self._active_turn_id}, timeout=5)
            self._active_turn_id = None
            self._add_event("event", "Pause", "Pause requested from Steam Deck.", "pending")
        else:
            self._add_event("event", "Pause", "No active turn to pause.", "")

    def _status_from_thread(self, thread: dict[str, Any]) -> str:
        raw = thread.get("status")
        status_type = raw.get("type") if isinstance(raw, dict) else raw
        if status_type == "active":
            return "working"
        if status_type == "idle":
            return "idle"
        if status_type == "systemError":
            return "disconnected"
        return "idle"

    def _task_from_thread(self, thread: dict[str, Any], status: str) -> str:
        if self._pending_approval:
            return self._pending_approval.get("text") or "Approval needed"
        if status == "working":
            active_item = self._latest_transcript_item(thread, {"command", "tool", "assistant", "plan", "reasoning"})
            if active_item:
                title = active_item.get("title") or "Codex"
                body = self._one_line(active_item.get("body") or "")
                return f"{title}: {body}" if body else f"{title} is running"
            return "Codex is working"
        latest_item = self._latest_transcript_item(thread, {"assistant", "command", "tool", "file", "plan", "user"})
        if latest_item:
            title = latest_item.get("title") or "Codex"
            body = self._one_line(latest_item.get("body") or "")
            if body:
                return f"Last: {title} - {body}"
        return "Connected to Codex App Server"

    def _latest_transcript_item(self, thread: dict[str, Any], kinds: set[str]) -> dict[str, Any] | None:
        for turn in reversed(thread.get("turns") or []):
            for item in reversed(turn.get("items") or []):
                transcript_item = self._transcript_item(item)
                if transcript_item and transcript_item.get("kind") in kinds and transcript_item.get("body"):
                    return transcript_item
        return None

    def _one_line(self, value: str) -> str:
        cleaned = " ".join(str(value).split())
        return self._truncate(cleaned, 110)

    def _find_active_turn_id(self, thread: dict[str, Any]) -> str | None:
        for turn in reversed(thread.get("turns") or []):
            if turn.get("status") == "inProgress":
                return turn.get("id")
        return None

    def _transcript_from_thread(self, thread: dict[str, Any]) -> list[dict[str, Any]]:
        transcript: list[dict[str, Any]] = []
        for turn in thread.get("turns") or []:
            for item in turn.get("items") or []:
                transcript_item = self._transcript_item(item)
                if transcript_item:
                    transcript.append(transcript_item)
        return transcript[-80:]

    def _transcript_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        item_id = str(item.get("id") or f"item-{len(str(item))}")
        item_type = item.get("type")
        if item_type == "userMessage":
            return self._feed_item(item_id, "user", "You", self._user_message_text(item), "sent")
        if item_type in {"agentMessage", "assistantMessage"}:
            return self._feed_item(item_id, "assistant", "Codex", str(item.get("text") or item.get("message") or "").strip(), str(item.get("phase") or ""))
        if item_type == "reasoning":
            summary = " ".join(str(part) for part in (item.get("summary") or item.get("content") or []) if part)
            return self._feed_item(item_id, "reasoning", "Reasoning", summary, "")
        if item_type == "plan":
            return self._feed_item(item_id, "plan", "Plan", str(item.get("text") or "").strip(), "updated")
        if item_type in {"commandExecution", "execCommand"}:
            command = str(item.get("command") or item.get("cmd") or "").strip()
            output = str(item.get("aggregatedOutput") or "").strip()
            body = command if not output else f"{command}\n\n{self._truncate(output, 900)}"
            status = str(item.get("status") or item.get("exitCode") or "")
            return self._feed_item(item_id, "command", "Command", body, status)
        if item_type == "fileChange":
            changes = item.get("changes") or []
            body = f"{len(changes)} file change(s)" if changes else "File changes"
            return self._feed_item(item_id, "file", "File changes", body, str(item.get("status") or ""))
        if item_type in {"mcpToolCall", "dynamicToolCall", "collabAgentToolCall"}:
            namespace = item.get("server") or item.get("namespace") or "tool"
            tool = item.get("tool") or item_type
            body = self._tool_body(item)
            return self._feed_item(item_id, "tool", f"{namespace}.{tool}", body, str(item.get("status") or ""))
        if item_type == "webSearch":
            return self._feed_item(item_id, "tool", "Web search", str(item.get("query") or ""), "completed")
        if item_type == "imageGeneration":
            return self._feed_item(item_id, "tool", "Image generation", str(item.get("result") or item.get("savedPath") or ""), str(item.get("status") or ""))
        if item_type in {"enteredReviewMode", "exitedReviewMode", "contextCompaction"}:
            return self._feed_item(item_id, "event", self._humanize(item_type), "", "")
        return None

    def _item_text(self, item: dict[str, Any]) -> str | None:
        item_type = item.get("type")
        if item_type in {"userMessage", "agentMessage", "assistantMessage"}:
            text = item.get("text") or item.get("message")
            if text:
                prefix = "You" if item_type == "userMessage" else "Codex"
                return f"{prefix}: {str(text).strip()[:180]}"
        if item_type in {"commandExecution", "execCommand"}:
            command = item.get("command") or item.get("cmd")
            status = item.get("status")
            if command:
                return f"Command {status}: {command}"
        if item_type == "planUpdate":
            return "Plan updated"
        return None

    def _user_message_text(self, item: dict[str, Any]) -> str:
        if item.get("text") or item.get("message"):
            return str(item.get("text") or item.get("message")).strip()
        parts: list[str] = []
        for content in item.get("content") or []:
            if isinstance(content, dict):
                text = content.get("text") or content.get("inputText") or content.get("path")
                if text:
                    parts.append(str(text))
            elif content:
                parts.append(str(content))
        return "\n".join(parts).strip()

    def _tool_body(self, item: dict[str, Any]) -> str:
        pieces: list[str] = []
        arguments = item.get("arguments")
        if arguments not in (None, "", {}):
            try:
                pieces.append(json.dumps(arguments, ensure_ascii=False, indent=2)[:900])
            except Exception:
                pieces.append(str(arguments)[:900])
        error = item.get("error")
        if error:
            pieces.append(f"Error: {self._truncate(str(error), 500)}")
        result = item.get("result") or item.get("contentItems") or item.get("agentsStates")
        if result not in (None, "", {}, []):
            try:
                pieces.append(self._truncate(json.dumps(result, ensure_ascii=False, indent=2), 900))
            except Exception:
                pieces.append(self._truncate(str(result), 900))
        prompt = item.get("prompt")
        if prompt:
            pieces.append(self._truncate(str(prompt), 900))
        return "\n\n".join(pieces)

    def _feed_item(self, item_id: str, kind: str, title: str, body: str, status: str) -> dict[str, Any]:
        return {
            "id": item_id,
            "kind": kind,
            "title": title,
            "body": self._truncate(body or "", 1600),
            "status": status or "",
        }

    def _append_stream_delta(self, kind: str, delta: str) -> None:
        if not delta:
            return
        with self._lock:
            title = "Reasoning" if kind == "reasoning" else "Codex"
            if not self._stream_item or self._stream_item.get("kind") != kind:
                self._finish_stream_item_locked()
                self._stream_item = self._feed_item(f"stream-{time.time_ns()}", kind, title, "", "streaming")
            self._stream_item["body"] = self._truncate(f"{self._stream_item.get('body', '')}{delta}", 1600)
            self._last_state["transcript"] = (self._last_state.get("transcript") or [])[-79:] + [self._stream_item]
            if self._stream_item["body"].strip():
                self._last_state["messages"] = [self._stream_item["body"][-220:]]

    def _finish_stream_item(self) -> None:
        with self._lock:
            self._finish_stream_item_locked()

    def _finish_stream_item_locked(self) -> None:
        if not self._stream_item:
            return
        finished = dict(self._stream_item)
        finished["status"] = "completed"
        self._live_items.append(finished)
        self._live_items = self._live_items[-20:]
        self._stream_item = None

    def _add_event(self, kind: str, title: str, body: str, status: str) -> None:
        item = self._feed_item(f"event-{time.time_ns()}", kind, title, body, status)
        with self._lock:
            self._live_items.append(item)
            self._live_items = self._live_items[-20:]
            self._last_state["transcript"] = (self._last_state.get("transcript") or [])[-79:] + [item]
        self._add_message(f"{title}: {body}" if body else title)

    def _truncate(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return f"{value[: limit - 3]}..."

    def _humanize(self, value: str) -> str:
        out = []
        for index, char in enumerate(value):
            if index and char.isupper():
                out.append(" ")
            out.append(char)
        return "".join(out).strip().capitalize()

    def _add_message(self, message: str) -> None:
        if not message:
            return
        with self._lock:
            self._messages.append(message[:220])
            self._messages = self._messages[-8:]

    def _account_message(self, account_response: dict[str, Any]) -> str:
        account = account_response.get("account")
        if not account:
            return "Not signed in to Codex."
        account_type = account.get("type")
        if account_type == "chatgpt":
            email = account.get("email") or "ChatGPT"
            plan = account.get("planType")
            return f"Signed in as {email}{f' ({plan})' if plan else ''}."
        if account_type == "apiKey":
            return "Signed in with API key."
        return f"Signed in with {account_type}."

    def _send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._send_frame(0x1, data)

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        sock = self._sock
        if not sock:
            raise RuntimeError("Socket is not connected.")
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
        mask = os.urandom(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        sock.sendall(bytes(header) + masked)

    def _read_frame(self, sock: socket.socket | ssl.SSLSocket) -> tuple[int, bytes]:
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

    def _read_exact(self, sock: socket.socket | ssl.SSLSocket, count: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < count:
            chunk = sock.recv(count - len(chunks))
            if not chunk:
                raise RuntimeError("Socket closed.")
            chunks.extend(chunk)
        return bytes(chunks)
