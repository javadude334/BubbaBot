"""Offline, interactive conversation with Bubba. Never connects to MRC.

Run: python -m bubbabot.chat
Reads OPENAI_API_KEY from the process environment. Do not pass keys on CLI.
"""
import json
import os
import sys
import urllib.error
import urllib.request

from .ai_provider import API_URL, FALLBACK, INSTRUCTIONS

MAX_TURNS = 6
MAX_REQUESTS = 20


def converse(messages, *, api_key, model="gpt-6-luna", transport=None, instructions=None):
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    payload = {
        "model": model,
        "instructions": instructions if instructions is not None else INSTRUCTIONS,
        "input": messages[-MAX_TURNS * 2:],
        "max_output_tokens": 160,
        "store": False,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "application/json"},
        method="POST",
    )
    transport = transport or urllib.request.urlopen
    try:
        with transport(request, timeout=25) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("OpenAI request failed (HTTP %s); check billing, model access, and project permissions." % exc.code) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise RuntimeError("OpenAI request failed (%s)." % type(exc).__name__) from None
    text = " ".join(
        part.get("text", "")
        for item in data.get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    ).strip()
    if not text:
        raise RuntimeError("OpenAI returned no text response.")
    return text[:350], data.get("usage", {})


def main():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("Missing OPENAI_API_KEY. Load it from /etc/bubbabot/openai.env securely.")
        return 1
    model = os.environ.get("BUBBABOT_AI_MODEL", "gpt-6-luna")
    history = []
    requests = 0
    tokens = 0
    print("BubbaBot — local AI chat (no MRC connection)")
    print("Commands: /quit, /reset, /usage. Up to %s API requests per session." % MAX_REQUESTS)
    while requests < MAX_REQUESTS:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in ("/quit", "/exit"):
            break
        if message.lower() == "/reset":
            history.clear()
            print("Conversation history cleared.")
            continue
        if message.lower() == "/usage":
            print("Requests: %s/%s; reported tokens: %s (not a monthly spending cap)" % (requests, MAX_REQUESTS, tokens))
            continue
        if not message or len(message) > 1000:
            print("Enter a message between 1 and 1000 characters.")
            continue
        candidate = history + [{"role": "user", "content": message}]
        requests += 1
        try:
            reply, usage = converse(candidate, api_key=key, model=model)
        except RuntimeError as exc:
            print("Error:", exc)
            continue
        history = (candidate + [{"role": "assistant", "content": reply}])[-MAX_TURNS * 2:]
        tokens += usage.get("total_tokens", 0)
        print("Bubba:", reply)
    if requests >= MAX_REQUESTS:
        print("Session request limit reached. Exit and restart to continue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
