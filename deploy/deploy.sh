#!/usr/bin/env bash
# Deploy both BubbaBot MRC connectors from GitHub main.
# Both services share /opt/bubbabot and its virtualenv.
set -Eeuo pipefail

APP_DIR="/opt/bubbabot"
PYTHON="$APP_DIR/.venv/bin/python"
SERVICES=(bubbabot-local-mrc.service bubbabot.service)
LOCAL_UNIT_SOURCE="$APP_DIR/deploy/bubbabot-local-mrc.service"
LOCAL_UNIT_TARGET="/etc/systemd/system/bubbabot-local-mrc.service"
OLD_REV=""
UPDATED=0
RESTART_STARTED=0
declare -a WAS_ACTIVE=()

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo bash $APP_DIR/deploy/deploy.sh" >&2
  exit 1
fi

cd "$APP_DIR"
git_safe() { git -c safe.directory="$APP_DIR" "$@"; }
[[ -x "$PYTHON" ]] || { echo "Missing virtualenv: $PYTHON" >&2; exit 1; }
[[ -r /etc/bubbabot/openai.env ]] || { echo "Missing local MRC environment file" >&2; exit 1; }
[[ -r /etc/bubbabot/bubbabot.env ]] || { echo "Missing official MRC environment file" >&2; exit 1; }
[[ -f "$LOCAL_UNIT_SOURCE" ]] || { echo "Missing local service unit" >&2; exit 1; }
for service in "${SERVICES[@]}"; do
  systemctl cat "$service" >/dev/null || { echo "Missing service: $service" >&2; exit 1; }
  if systemctl is-active --quiet "$service"; then WAS_ACTIVE+=(1); else WAS_ACTIVE+=(0); fi
done

# Never overwrite local tracked changes, including staged changes.
if [[ -n "$(git_safe status --porcelain --untracked-files=no)" ]]; then
  echo "Tracked local modifications detected; refusing to deploy." >&2
  exit 1
fi
if [[ "$(git_safe branch --show-current)" != "main" ]]; then
  echo "Expected checkout on main; refusing to deploy." >&2
  exit 1
fi

OLD_REV="$(git_safe rev-parse HEAD)"

rollback() {
  local code=$?
  trap - ERR
  if (( code == 0 )); then return; fi
  echo "Deployment failed (exit $code)." >&2
  if (( UPDATED )); then
    echo "Restoring previous checkout $OLD_REV..." >&2
    git_safe reset --hard "$OLD_REV" || true
    # Restore local unit if code changed it.
    if [[ -f "$LOCAL_UNIT_SOURCE" ]]; then
      install -m 0644 "$LOCAL_UNIT_SOURCE" "$LOCAL_UNIT_TARGET" || true
      systemctl daemon-reload || true
    fi
  fi
  if (( RESTART_STARTED )); then
    echo "Restoring previously running services..." >&2
    for i in "${!SERVICES[@]}"; do
      if [[ "${WAS_ACTIVE[$i]}" == 1 ]]; then
        systemctl restart "${SERVICES[$i]}" || true
      fi
    done
  fi
  exit "$code"
}
trap rollback ERR

echo "Fetching latest BubbaBot..."
git_safe fetch origin main
# Refuse non-fast-forward deployments before touching services.
git_safe merge-base --is-ancestor "$OLD_REV" origin/main || {
  echo "origin/main is not a fast-forward of this checkout." >&2
  exit 1
}
if [[ "$OLD_REV" != "$(git_safe rev-parse origin/main)" ]]; then
  git_safe merge --ff-only origin/main
  UPDATED=1
fi

echo "Running offline tests (services stay online)..."
"$PYTHON" -m unittest discover -s tests -v

# Install the version-controlled local unit; preserve the existing official unit.
install -m 0644 "$LOCAL_UNIT_SOURCE" "$LOCAL_UNIT_TARGET"
systemctl daemon-reload

# Stop old transient test instances so they cannot duplicate replies.
for old in bubbabot-mrc-test.service bubbabot-mrc-test2.service bubbabot-mrc-test3.service; do
  systemctl stop "$old" 2>/dev/null || true
done

echo "Restarting both MRC connectors..."
RESTART_STARTED=1
for service in "${SERVICES[@]}"; do
  systemctl restart "$service"
done
sleep 2
for service in "${SERVICES[@]}"; do
  systemctl is-active --quiet "$service" || {
    echo "$service did not stay active" >&2
    false
  }
done

trap - ERR
echo "Deployment complete at $(git_safe rev-parse --short HEAD)."
systemctl --no-pager --full status "${SERVICES[@]}" || true
echo "Logs: sudo journalctl -u bubbabot.service -u bubbabot-local-mrc.service -f"
