"""Offline adapter integration tests with mocked HTTP. No paid API requests."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from bubbabot.ai.base import AIError
from bubbabot.ai.ollama_provider import OllamaProvider
from bubbabot.ai.openai_provider import OpenAIProvider


class FakeHTTP:
    def __init__(self, data):
        self.data = io.BytesIO(json.dumps(data).encode())

    def __enter__(self):
        return self.data

    def __exit__(self, *args):
        self.data.close()


class AdapterTests(unittest.TestCase):
    @patch("bubbabot.ai.ollama_provider.urlopen")
    def test_ollama_success(self, urlopen):
        urlopen.return_value = FakeHTTP({"message": {"content": "Howdy!"},
                                         "prompt_eval_count": 30, "eval_count": 8})
        response = OllamaProvider().generate([{"role": "user", "content": "Hi"}])
        self.assertEqual(response.provider, "ollama")
        self.assertEqual(response.text, "Howdy!")
        self.assertEqual(response.output_tokens, 8)

    @patch("bubbabot.ai.openai_provider.urlopen")
    def test_openai_success(self, urlopen):
        urlopen.return_value = FakeHTTP({"choices": [{"message": {"content": "Howdy!"}}],
                                         "usage": {"prompt_tokens": 10, "completion_tokens": 4}})
        response = OpenAIProvider("fake-test-key").generate([{"role": "user", "content": "Hi"}])
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.input_tokens, 10)

    @patch("bubbabot.ai.openai_provider.urlopen")
    def test_quota_normalized(self, urlopen):
        error = HTTPError("https://example.invalid", 429, "Quota", {},
                          io.BytesIO(b'{"error":{"code":"insufficient_quota"}}'))
        urlopen.side_effect = error
        with self.assertRaises(AIError) as caught:
            OpenAIProvider("fake-test-key").generate([])
        self.assertEqual(caught.exception.category, "quota")

    @patch("bubbabot.ai.ollama_provider.urlopen", side_effect=URLError("offline"))
    def test_ollama_offline(self, urlopen):
        with self.assertRaises(AIError) as caught:
            OllamaProvider().generate([])
        self.assertEqual(caught.exception.category, "unavailable")


if __name__ == "__main__":
    unittest.main()
