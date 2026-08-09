import unittest

from codex_remote.application.transcript_mapper import TranscriptMapper


class TranscriptMapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = TranscriptMapper()

    def test_maps_user_message_content_parts(self) -> None:
        item = {
            "id": "u1",
            "type": "userMessage",
            "content": [{"text": "Hello"}, {"path": "src/index.tsx"}],
        }

        self.assertEqual(
            self.mapper.item_to_transcript(item),
            {"id": "u1", "kind": "user", "title": "You", "body": "Hello\nsrc/index.tsx", "status": "sent"},
        )

    def test_maps_command_with_truncated_output(self) -> None:
        item = {
            "id": "c1",
            "type": "commandExecution",
            "command": "pnpm test",
            "aggregatedOutput": "x" * 1000,
            "status": "completed",
        }

        result = self.mapper.item_to_transcript(item)

        self.assertIsNotNone(result)
        self.assertEqual(result["kind"], "command")
        self.assertEqual(result["title"], "Command")
        self.assertTrue(result["body"].startswith("pnpm test\n\n"))
        self.assertLessEqual(len(result["body"]), 1600)
        self.assertEqual(result["status"], "completed")

    def test_maps_tool_call_arguments_and_result(self) -> None:
        item = {
            "id": "t1",
            "type": "mcpToolCall",
            "server": "web",
            "tool": "search",
            "arguments": {"q": "Codex"},
            "result": {"ok": True},
            "status": "completed",
        }

        result = self.mapper.item_to_transcript(item)

        self.assertIsNotNone(result)
        self.assertEqual(result["kind"], "tool")
        self.assertEqual(result["title"], "web.search")
        self.assertIn('"q": "Codex"', result["body"])
        self.assertIn('"ok": true', result["body"])

    def test_uses_codex_chat_fallback_title(self) -> None:
        title = self.mapper.thread_title({"id": "abcdef123456"})

        self.assertEqual(title, "Codex chat abcdef")


if __name__ == "__main__":
    unittest.main()
