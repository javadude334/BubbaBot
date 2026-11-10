import io
import json
import unittest
from unittest.mock import patch
from bubbabot.ai_provider import BubbaAI, FALLBACK, API_URL


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AITests(unittest.TestCase):
    def test_no_key_no_network(self):
        self.assertEqual(BubbaAI(api_key="", transport=lambda *a, **k: self.fail("network")).reply("hi"), FALLBACK)

    def test_request_shape_and_reply(self):
        calls = []
        def transport(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(json.dumps({"output": [{"type": "message", "content": [{"type": "output_text", "text": "Howdy, friend!"}]}]}).encode())
        self.assertEqual(BubbaAI(api_key="test-key", transport=transport).reply("hello"), "Howdy, friend!")
        request, timeout = calls[0]
        self.assertEqual(request.full_url, API_URL)
        payload = json.loads(request.data)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["input"][0]["content"], "hello")
        self.assertNotIn("test-key", request.data.decode())

    def test_network_error_fallback(self):
        def broken(*args, **kwargs):
            raise OSError("offline")
        self.assertEqual(BubbaAI(api_key="test-key", transport=broken).reply("hello"), FALLBACK)

    def test_invalid_message_no_network(self):
        self.assertEqual(BubbaAI(api_key="test-key", transport=lambda *a, **k: self.fail("network")).reply("x"*1001), FALLBACK)

    def test_empty_output_fallback(self):
        def transport(*args, **kwargs):
            return FakeResponse(b'{"output":[]}')
        self.assertEqual(BubbaAI(api_key="test-key", transport=transport).reply("hello"), FALLBACK)


if __name__ == "__main__":
    unittest.main()
