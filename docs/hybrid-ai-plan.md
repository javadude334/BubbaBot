# Hybrid AI implementation plan (2026-11-10)

Status: design only; no live MRC or paid API calls.

## Decisions
- Cloud primary: low-cost OpenAI API model (model ID configurable).
- Local fallback: Ollama on Windows host (i5-10400, 32 GB RAM, GTX 1070 Ti 8 GB VRAM), initially test a quantized 3–4B model.
- Cloud spending target: USD $1/calendar month, warning at $0.75. App-side estimate is **not** a guaranteed provider billing cap.
- Preserve personality and approved memory in BubbaBot, independent of provider.
- Keep provider selection configurable for future Gemini/Groq adapters.

## Suggested Python modules
- `bubbabot/ai/base.py`: provider protocol, request/response objects, normalized error categories.
- `bubbabot/ai/openai_provider.py`: cloud adapter with explicit timeouts and token usage accounting.
- `bubbabot/ai/ollama_provider.py`: local HTTP adapter with configurable URL and model.
- `bubbabot/ai/router.py`: cloud-first routing, retry/backoff, failover on quota/timeout/outage.
- `bubbabot/ai/budget.py`: persistent monthly ledger, estimated preflight reservation and post-response reconciliation.
- `bubbabot/personality.py`: shared system prompt and bounded context; no provider-specific memory.
- `tests/test_ai_router.py`: fake-provider tests requiring no network or API keys.

## Failure and safety behavior
- Quota exhausted or app budget exceeded: use Ollama until next budget period or deliberate operator reset.
- Rate limit/transient server error: short backoff/circuit breaker, then local fallback.
- Invalid API key: report configuration error; optionally use local fallback, do not retry rapidly.
- Ollama unavailable: send a bounded friendly unavailable message; do not loop.
- Never send the same request to both providers concurrently; no unbounded retries.
- Track token usage and price per model; price changes require configuration updates.
- Avoid storing secrets, private chat logs or personal memory in the repository.
- Restrict Ollama listener to localhost or a private authenticated tunnel, not a public port.
- Include per-user/channel cooldowns, response length limits and opt-in live MRC connection.
- Confirm current MRC operator bot policy and handshake before any public connection.

## Implementation sequence
1. Add provider interfaces, fake adapters, budget and routing tests.
2. Integrate OpenAI and Ollama adapters behind environment-based configuration.
3. Benchmark local latency, GPU memory and conversation quality; tune prompt/context.
4. Simulate quota exhaustion and month rollover; verify automatic recovery.
5. Only after operator permission, test in sanctioned MRC room.

## Example configuration keys (no secrets)
`AI_PRIMARY=openai`, `AI_FALLBACK=ollama`, `AI_MONTHLY_USD=1.00`, `AI_WARN_USD=0.75`, `OLLAMA_BASE_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL=<tested-model>`, `OPENAI_MODEL=<priced-low-cost-model>`.
