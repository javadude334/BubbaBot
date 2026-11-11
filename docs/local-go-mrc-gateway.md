# Local Go MRC gateway integration (experimental)

This adapter connects the Ubuntu BubbaBot to a **privately operated Go MRC gateway** for local testing. It does not connect to the public MRC network and does not replace the approved official SDK connector.

## Components

- `bubbabot/lan_mrc_adapter.py`: TCP transport and terminal-safe output
- `bubbabot/engine.py`: mention, room and rate-limit decisions
- `bubbabot/chat.py`: OpenAI Responses API calls
- `bubbabot/official_sdk_runner.py`: **unchanged** official connector

The adapter accepts mentions in `#bubba` to start a per-user conversation, then accepts follow-up messages without another mention for 10 minutes after each successful reply. Sessions and conversation history are keyed by site and username and are held only in process memory. It ignores self/server messages and does not handle private messages. It uses a 5-second per-sender cooldown, retains the 20 replies/hour global limit, and adds a 100-attempt process-lifetime limit. **These limits do not enforce a dollar budget.** It stores short histories in memory only and converts outgoing chat to printable ASCII for Mystic compatibility.

## Run manually on Ubuntu

Install or update the repository into `/opt/bubbabot`, preserving existing environment files. The existing key is stored outside the repository at `/etc/bubbabot/openai.env`. Never commit or print the key.

For a local test, run the Python module as the `bubbabot` account with a systemd transient service:

```sh
sudo systemd-run --unit=bubbabot-mrc-test --collect \
  -p User=bubbabot -p Group=bubbabot \
  -p WorkingDirectory=/opt/bubbabot \
  -p EnvironmentFile=/etc/bubbabot/openai.env \
  -p Environment=LOCAL_MRC_HOST=192.168.150.58 \
  -p Environment=LOCAL_MRC_PORT=5000 \
  /opt/bubbabot/.venv/bin/python -u -m bubbabot.lan_mrc_adapter
```

Replace the sample LAN address for your gateway. Keep the original `bubbabot.service` stopped while testing. Confirm with `sudo journalctl -u bubbabot-mrc-test -n 30 --no-pager`. Stop with `sudo systemctl stop bubbabot-mrc-test`.

## Security and deployment gates

- Bind the gateway to a LAN interface and allow TCP/5000 only from the trusted Ubuntu host. The current Go protocol is **plaintext and unauthenticated**; do not port-forward it or expose it publicly.
- The Go server currently broadcasts non-control packets to all connected peers; proper server-side room routing and sender identity validation are outstanding.
- Confirm formatting, 10-minute conversation sessions, reconnect behavior, cooldowns, and OpenAI error handling in the sandbox.
- Verify approval and exact conditions with the public MRC network operator before any live-network connection. Approval is **not** implied by successful LAN testing.
- After approval, implement and test a dedicated authorized connector; do not point this LAN-only adapter at the public service or weaken the existing SDK TLS/room restrictions.
- Before production, implement persistent usage/spend safeguards and deployment monitoring.
