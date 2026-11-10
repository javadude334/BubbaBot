"""Interactive local conversation tester; cloud is explicit opt-in."""
import argparse
import os
from pathlib import Path
from .ai.base import AIError
from .ai.budget import MonthlyBudget
from .ai.ollama_provider import OllamaProvider
from .ai.openai_provider import OpenAIProvider
from .ai.prompt import build_messages
from .ai.router import AIRouter
from .personality import Personality


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud", action="store_true",
                        help="Opt into paid OpenAI API; default uses local Ollama only")
    args = parser.parse_args()
    local = OllamaProvider(os.getenv("OLLAMA_MODEL", "qwen3:4b"),
                           os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    provider = local
    if args.cloud:
        cloud = OpenAIProvider(os.getenv("OPENAI_API_KEY", ""),
                               os.getenv("OPENAI_MODEL", "gpt-4.1-nano"))
        budget = MonthlyBudget(os.getenv("AI_BUDGET_FILE", str(Path.home() / ".bubbabot" / "budget.json")),
                               os.getenv("AI_MONTHLY_USD", "1.00"), os.getenv("AI_WARN_USD", "0.75"))
        provider = AIRouter(cloud, local, budget, os.getenv("AI_ESTIMATED_CALL_USD", "0.01"))
    history, bubba = [], Personality()
    print("Bubba local chat; /quit to exit. No MRC connection.")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if prompt.lower() in ("/quit", "/exit"):
            break
        if not prompt:
            continue
        canned = bubba.respond("local-user", prompt)
        if canned is not None:
            print("Bubba: " + canned)
            continue
        try:
            response = provider.generate(build_messages(prompt, history))
            print(f"Bubba ({response.provider}): {response.text}")
            history.extend([{"role": "user", "content": prompt},
                            {"role": "assistant", "content": response.text}])
            history = history[-8:]
        except AIError as exc:
            print(f"Bubba unavailable ({exc.category}); check provider configuration.")


if __name__ == "__main__":
    main()
