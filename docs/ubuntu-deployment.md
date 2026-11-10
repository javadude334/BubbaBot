# BubbaBot Ubuntu deployment preparation (offline only)

The application is **not ready to connect to public MRC**. All network settings are restricted to numeric loopback IP addresses. Do not open a firewall port, add a public hostname, or deploy an always-on live bot until the MRC operator confirms its connector protocol and rules.

## Development prerequisites

- Python 3.10 or newer
- Clone the repository and run `python3 -m unittest discover -s tests -v`
- Copy `bubba.local.example.json` to `bubba.local.json`
- Run the interactive mock server: `python3 -m bubbabot.local_test_server`
- In a second terminal: `python3 -m bubbabot.local_runner --config bubba.local.json`

## Operations

- Log file: `logs/bubbabot.log` with rotating files (3 backups of 500 KB)
- Stop: Ctrl+C
- Chat content is not written to event logs
- No credentials or API keys are required
- Local reconnect is bounded and opt-in via `--max-sessions`

Do not create a production systemd service yet. When the operator provides approved client registration, TLS requirements, and room join behavior, add a separate live adapter, secrets via environment or service credentials, and a systemd unit with least-privilege permissions.
