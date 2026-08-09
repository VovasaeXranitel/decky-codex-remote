import json
import os
from typing import Any


class TranscriptMapper:
    def transcript_from_thread(self, thread: dict[str, Any]) -> list[dict[str, Any]]:
        transcript: list[dict[str, Any]] = []
        for turn in thread.get("turns") or []:
            for item in turn.get("items") or []:
                transcript_item = self.item_to_transcript(item)
                if transcript_item:
                    transcript.append(transcript_item)
        return transcript[-80:]

    def latest_transcript_item(self, thread: dict[str, Any], kinds: set[str]) -> dict[str, Any] | None:
        for turn in reversed(thread.get("turns") or []):
            for item in reversed(turn.get("items") or []):
                transcript_item = self.item_to_transcript(item)
                if transcript_item and transcript_item.get("kind") in kinds and transcript_item.get("body"):
                    return transcript_item
        return None

    def item_to_transcript(self, item: dict[str, Any]) -> dict[str, Any] | None:
        item_id = str(item.get("id") or f"item-{len(str(item))}")
        item_type = item.get("type")
        if item_type == "userMessage":
            return self._feed_item(item_id, "user", "You", self.user_message_text(item), "sent")
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
            body = command if not output else f"{command}\n\n{self.truncate(output, 900)}"
            status = str(item.get("status") or item.get("exitCode") or "")
            return self._feed_item(item_id, "command", "Command", body, status)
        if item_type == "fileChange":
            changes = item.get("changes") or []
            body = f"{len(changes)} file change(s)" if changes else "File changes"
            return self._feed_item(item_id, "file", "File changes", body, str(item.get("status") or ""))
        if item_type in {"mcpToolCall", "dynamicToolCall", "collabAgentToolCall"}:
            namespace = item.get("server") or item.get("namespace") or "tool"
            tool = item.get("tool") or item_type
            body = self.tool_body(item)
            return self._feed_item(item_id, "tool", f"{namespace}.{tool}", body, str(item.get("status") or ""))
        if item_type == "webSearch":
            return self._feed_item(item_id, "tool", "Web search", str(item.get("query") or ""), "completed")
        if item_type == "imageGeneration":
            return self._feed_item(item_id, "tool", "Image generation", str(item.get("result") or item.get("savedPath") or ""), str(item.get("status") or ""))
        if item_type in {"enteredReviewMode", "exitedReviewMode", "contextCompaction"}:
            return self._feed_item(item_id, "event", self.humanize(item_type), "", "")
        return None

    def thread_title(self, thread: dict[str, Any]) -> str:
        for key in ("name", "preview"):
            value = thread.get(key)
            if isinstance(value, str) and value.strip():
                return self.clean_thread_title(value)
        cwd = thread.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            return os.path.basename(cwd.rstrip("/")) or cwd
        thread_id = str(thread.get("id") or "")
        if thread_id:
            return f"Codex chat {thread_id[:6]}"
        return "Untitled chat"

    def clean_thread_title(self, value: str) -> str:
        collapsed = " ".join(value.strip().split())
        if len(collapsed) > 72:
            return f"{collapsed[:69]}..."
        return collapsed

    def user_message_text(self, item: dict[str, Any]) -> str:
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

    def tool_body(self, item: dict[str, Any]) -> str:
        pieces: list[str] = []
        arguments = item.get("arguments")
        if arguments not in (None, "", {}):
            try:
                pieces.append(json.dumps(arguments, ensure_ascii=False, indent=2)[:900])
            except Exception:
                pieces.append(str(arguments)[:900])
        error = item.get("error")
        if error:
            pieces.append(f"Error: {self.truncate(str(error), 500)}")
        result = item.get("result") or item.get("contentItems") or item.get("agentsStates")
        if result not in (None, "", {}, []):
            try:
                pieces.append(self.truncate(json.dumps(result, ensure_ascii=False, indent=2), 900))
            except Exception:
                pieces.append(self.truncate(str(result), 900))
        prompt = item.get("prompt")
        if prompt:
            pieces.append(self.truncate(str(prompt), 900))
        return "\n\n".join(pieces)

    def feed_item(self, item_id: str, kind: str, title: str, body: str, status: str) -> dict[str, Any]:
        return self._feed_item(item_id, kind, title, body, status)

    def truncate(self, value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return f"{value[: limit - 3]}..."

    def humanize(self, value: str) -> str:
        out = []
        for index, char in enumerate(value):
            if index and char.isupper():
                out.append(" ")
            out.append(char)
        return "".join(out).strip().capitalize()

    def _feed_item(self, item_id: str, kind: str, title: str, body: str, status: str) -> dict[str, Any]:
        return {
            "id": item_id,
            "kind": kind,
            "title": title,
            "body": self.truncate(body or "", 1600),
            "status": status or "",
        }
