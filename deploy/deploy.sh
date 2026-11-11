#!/usr/bin/env bash
# Deploy BubbaBot's private-LAN MRC adapter from the default GitHub branch.
set -Eeuo pipefail

APP_DIR="/opt/bubbabot"
SERVICE="bubbabot-local-mrc.service"
PYTHON="$APP_DIR/.venv/bin/python"
UNIT_SOURCE="$APP_DIR/deploy/bubbabot-local-mrc.service"
UNIT_TARGET="/etc/systemd/system/$SERVICE"

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo bash $APP_DIR/deploy/deploy.sh" >&2
  exit 1
fi

cd "$APP_DIR"
[[ -x "$PYTHON" ]] || { echo "Missing virtualenv: $PYTHON" >&2; exit 1; }
[[ -r /etc/bubbabot/openai.env ]] || { echo "Missing OpenAI environment file" >&2; exit 1; }

# Never overwrite tracked local modifications. Untracked local SDK files are retained.
if [[ -n "$(git -c safe.directory="$APP_DIR" status --porcelain --untracked-files=no)" ]]; then
  echo "Tracked local modifications detected; refusing to deploy." >&2
  exit 1
fi

echo "Fetching latest BubbaBot..."
git -c safe.directory="$APP_DIR" fetch origin main
git -c safe.directory="$APP_DIR" merge --ff-only origin/main

echo "Running offline tests..."
"$PYTHON" -m unittest discover -s tests -v

echo "Installing systemd service..."
install -m 0644 "$UNIT_SOURCE" "$UNIT_TARGET"
systemctl daemon-reload

# Keep the original official-network service untouched.
if systemctl is-active --quiet bubbabot.service; then
  echo "Original bubbabot.service is active; stop it manually before deployment." >&2
  exit 1
fi

# Stop any prior transient test instances to prevent duplicate AI responses.
for old in bubbabot-mrc-test.service bubbabot-mrc-test2.service bubbabot-mrc-test3.service; do
  systemctl stop "$old" 2>/dev/null || true
done

systemctl enable "$SERVICE"
systemctl restart "$SERVICE"
systemctl --no-pager --full status "$SERVICE"
echo "Deployment complete. Follow logs: sudo journalctl -u $SERVICE -f"
