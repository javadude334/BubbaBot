# BubbaBot Ubuntu deployment

BubbaBot now has an **official MRC Mode 1 SDK adapter**, but public
connectivity must wait for the connector approval and credentials.

## Requirements

- Ubuntu with Python 3.10+, python3-venv, git
- Official SDK from https://github.com/stack-fault/mrc-connector-sdk
- Approved connector host, TLS port, slug, and token from StackFault
- No additional inbound router forwarding is expected; SDK uses outbound TLS

**Important:** `bubbachat.davesbbs.com` is the hostname submitted for
whitelisting. It is **not** the MRC server value for `CONNECTOR_HOST`.

## Install files and test offline

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv git
sudo useradd --system --home /opt/bubbabot --shell /usr/sbin/nologin bubbabot
sudo git clone https://github.com/javadude334/BubbaBot.git /opt/bubbabot
sudo chown -R bubbabot:bubbabot /opt/bubbabot
sudo -u bubbabot python3 -m venv /opt/bubbabot/.venv
cd /opt/bubbabot
sudo -u bubbabot .venv/bin/python -m unittest discover -s tests -v
```

If the repository is private, use your authorized GitHub authentication
method to clone it. Do not embed GitHub tokens in scripts or service files.

Copy the official upstream `mrc_connector/` directory into
`/opt/bubbabot/mrc_connector/` so that the Python SDK is importable.
Use the actual upstream SDK files rather than copying examples or
inventing an API.

## Configure after connector approval

```bash
sudo install -d -m 700 /etc/bubbabot
sudo install -m 600 /opt/bubbabot/deploy/bubbabot.env.example /etc/bubbabot/bubbabot.env
sudo nano /etc/bubbabot/bubbabot.env
```

Set `CONNECTOR_HOST`, `CONNECTOR_PORT`, `CONNECTOR_TOKEN`, and
`BOT_SLUG` to the values issued by the MRC administrator.
Keep `BOT_ROOM=bubba`. The runner enforces verified TLS.

The secret environment file should remain root-owned with mode 0600.
Systemd reads it before dropping privileges to the `bubbabot` user.

## Install systemd service

```bash
sudo cp /opt/bubbabot/deploy/bubbabot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

**Do not enable or start until approval and configuration are complete.**

After approval:

```bash
sudo systemctl enable --now bubbabot
sudo journalctl -u bubbabot -f
```

To stop: `sudo systemctl disable --now bubbabot`.

The service runs as an unprivileged account, restarts after failures,
and writes to the systemd journal. Avoid debug logging and do not
publish connector credentials. No AI API is used in the current runner.

The old local TCP simulator remains available for offline regression
tests but must not be used for the public MRC connector.
