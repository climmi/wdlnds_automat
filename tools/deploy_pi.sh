#!/usr/bin/env bash

set -euo pipefail

PI_HOST="${PI_HOST:-wdlnds-pi}"
PI_USER="${PI_USER:-qwert}"
REMOTE_DIR="${REMOTE_DIR:-}"
SERVICE="${SERVICE:-wdlnds-automat.service}"
SKIP_INSTALL=0
NO_RESTART=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      PI_HOST="$2"
      shift 2
      ;;
    --user)
      PI_USER="$2"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="$2"
      shift 2
      ;;
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    --no-restart)
      NO_RESTART=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./tools/deploy_pi.sh [options]

Options:
  --host <hostname>        Raspberry Pi hostname or IP
  --user <user>            SSH username
  --remote-dir <path>      Target directory on the Pi
  --service <name>         systemd service to restart
  --skip-install           Upload only, skip pip install
  --no-restart             Do not restart the systemd service
  -h, --help               Show this help
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "$REMOTE_DIR" ]]; then
  REMOTE_DIR="/home/$PI_USER/wdlnds_automat"
fi

ARCHIVE="$(mktemp -t wdlnds_automat_deploy.XXXXXX).zip"
cleanup() {
  rm -f "$ARCHIVE"
}
trap cleanup EXIT

echo "[1/5] Build deployment archive..."
pushd "$ROOT_DIR" >/dev/null
zip -qr "$ARCHIVE" . \
  -x ".git/*" \
  -x ".venv/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x ".DS_Store"
popd >/dev/null

echo "[2/5] Upload archive to Pi..."
scp "$ARCHIVE" "${PI_USER}@${PI_HOST}:~/wdlnds_automat_deploy.zip"

echo "[3/5] Extract project on Pi..."
ssh "${PI_USER}@${PI_HOST}" "mkdir -p '$REMOTE_DIR' && unzip -oq ~/wdlnds_automat_deploy.zip -d '$REMOTE_DIR'"

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  echo "[4/5] Ensure venv and install dependencies..."
  read -r -d '' INSTALL_CMD <<EOF || true
set -e
if [ ! -d '$REMOTE_DIR/.venv' ]; then
  python3 -m venv '$REMOTE_DIR/.venv'
fi
'$REMOTE_DIR/.venv/bin/python' -m pip install --upgrade pip
'$REMOTE_DIR/.venv/bin/python' -m pip install -r '$REMOTE_DIR/requirements.txt'
if [ -f '$REMOTE_DIR/requirements-pi.txt' ]; then
  '$REMOTE_DIR/.venv/bin/python' -m pip install -r '$REMOTE_DIR/requirements-pi.txt'
fi
EOF
  ssh "${PI_USER}@${PI_HOST}" "$INSTALL_CMD"
else
  echo "[4/5] Skip dependency install (--skip-install)."
fi

if [[ "$NO_RESTART" -eq 0 ]]; then
  echo "[5/5] Restart service and print status..."
  ssh "${PI_USER}@${PI_HOST}" "sudo systemctl restart '$SERVICE' && systemctl status '$SERVICE' --no-pager"
else
  echo "[5/5] Skip service restart (--no-restart)."
fi

echo "Done."
