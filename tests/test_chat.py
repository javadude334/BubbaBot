import io
import json
import unittest
from bubbabot.chat import converse, MAX_TURNS


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class ChatTests(unittest.TestCase):
    def test_history_and_usage(self):
        seen = []
        def transport(request, timeout):
            seen.append(json.loads(request.data))
            return FakeResponse(json.dumps({"output": [{"type": "message", "content": [{"type": "output_text", "text": "Howdy!"}]}], "usage": {"total_tokens": 27}}).encode())
        messages = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}, {"role": "user", "content": "Rufus?"}]
        reply, usage = converse(messages, api_key="fake", transport=transport)
        self.assertEqual(reply, "Howdy!")
        self.assertEqual(usage["total_tokens"], 27)
        self.assertEqual(seen[0]["input"], messages)
        self.assertFalse(seen[0]["store"])

    def test_history_is_bounded(self):
        seen = []
        def transport(request, timeout):
            seen.append(json.loads(request.data))
            return FakeResponse(b'{"output":[{"type":"message","content":[{"type":"output_text","text":"Hi"}]}]}')
        converse([{"role": "user", "content": str(i)} for i in range(30)], api_key="fake", transport=transport)
        self.assertEqual(len(seen[0]["input"]), MAX_TURNS * 2)

    def test_missing_key(self):
        with self.assertRaises(ValueError):
            converse([], api_key="")


if __name__ == "__main__":
    unittest.main()
