"""Ollama adapter, Python standard library only."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .base import AIError, AIResponse


class OllamaProvider:
    def __init__(self, model="qwen3:4b", base_url="http://127.0.0.1:11434", timeout=45):
        self.model, self.base_url, self.timeout = model, base_url.rstrip("/"), timeout

    def generate(self, messages):
        payload = json.dumps({"model": self.model, "messages": messages,
                              "stream": False, "options": {"num_predict": 120}}).encode()
        request = Request(self.base_url + "/api/chat", data=payload,
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
            return AIResponse(str(data["message"]["content"]).strip(), "ollama",
                              data.get("prompt_eval_count", 0), data.get("eval_count", 0))
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            raise AIError("unavailable", "Ollama request failed") from exc
