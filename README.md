# BubbaBot

Bubba is an experimental AI assistant for the Mystic Relay Chat (MRC) network. It is being built as a **standalone client**, so users from participating BBSes could eventually reach the same bot.

> **Status: v0.1.0 protocol foundation — offline only.** The public MRC server's policy on automated clients, independent client handshakes, bot naming and room access has **not yet been verified**. Do not connect Bubba to the live network until confirmed with its operator.

## First milestone

- Parse and serialize MRC's seven primary tilde-separated fields.
- Detect direct mentions of Bubba and filter rooms.
- Ignore control messages and Bubba's own messages to prevent loops.
- Test all of the above locally, with no API key, network connection, or usage charges.

## Layout

- `bubbabot/protocol.py` — packet representation and serialization
- `bubbabot/routing.py` — room, mention and loop checks
- `tests/` — offline unit tests
- `docs/architecture.md` — integration options and outstanding checks

## Quickstart

Python 3.10+ is recommended. No third-party packages are required for this milestone.

```powershell
git clone https://github.com/javadude334/BubbaBot.git
cd BubbaBot
python -m unittest discover -s tests -v
```

No live connection or OpenAI API call is made by the tests.

## Design notes

The BBS-side MRC multiplexer examined for this project (v1.3.7) exchanges seven positional fields:

`from_user~from_site~from_room~to_user~to_site~to_room~message~`

That observation alone does not establish the full server authentication/authorization protocol. In particular, the historical server distributed in `mrc_full.zip` is not proof of how the currently hosted MRC server operates.

## Security

Never commit MRC configuration files containing secrets, chat logs, tokens, API keys, or personal chat transcripts. Keep production configuration outside version control. AI-generated replies should clearly identify the bot as AI, be bounded in length, and enforce per-user rate limits plus an application-side spend ceiling before live deployment.

## Roadmap

1. Offline protocol and routing tests (this milestone).
2. Verify live network bot policy and protocol compatibility with MRC operators.
3. Add an isolated transport adapter, simulated integration tests, and explicit live mode opt-in.
4. Add OpenAI-backed responses, rate limits, budget controls, and logging.
5. Test in a sanctioned room, then deploy with restart/health monitoring.
