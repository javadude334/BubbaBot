"""OpenAI chat completions adapter; no external Python dependencies."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .base import AIError, AIResponse


class OpenAIProvider:
    def __init__(self, api_key, model="gpt-4.1-nano", timeout=30):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def generate(self, messages):
        payload = json.dumps({"model": self.model, "messages": messages,
                              "max_completion_tokens": 160}).encode()
        request = Request("https://api.openai.com/v1/chat/completions",
                          data=payload, method="POST",
                          headers={"Content-Type": "application/json",
                                   "Authorization": "Bearer " + self.api_key})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
            usage = data.get("usage", {})
            return AIResponse((data["choices"][0]["message"]["content"] or "").strip(),
                              "openai", usage.get("prompt_tokens", 0),
                              usage.get("completion_tokens", 0))
        except HTTPError as exc:
            try:
                code = json.loads(exc.read().decode()).get("error", {}).get("code")
            except (ValueError, UnicodeDecodeError):
                code = None
            category = ("quota" if code == "insufficient_quota" else
                        "auth" if exc.code in (401, 403) else
                        "rate_limit" if exc.code == 429 else
                        "unavailable" if exc.code >= 500 else "invalid_request")
            raise AIError(category, f"OpenAI HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AIError("timeout", "OpenAI connection unavailable") from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIError("unavailable", "Invalid OpenAI response") from exc
