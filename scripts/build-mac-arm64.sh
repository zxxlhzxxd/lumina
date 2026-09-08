#!/usr/bin/env bash
# Build the macOS arm64 installer.
# Usage:
#   ./scripts/build-mac-arm64.sh
#   ./scripts/build-mac-arm64.sh --bible /path/to/custom.lumina-bible
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BIBLE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bible)
      BIBLE="${2:-}"
      if [[ -z "$BIBLE" ]]; then
        echo "error: --bible 需要一个 .lumina-bible 路径" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      sed -n '2,6p' "$0"
      exit 0
      ;;
    *)
      echo "error: 未知参数 $1" >&2
      exit 1
      ;;
  esac
done

if [[ -n "$BIBLE" ]]; then
  BIBLE="$(cd "$(dirname "$BIBLE")" && pwd)/$(basename "$BIBLE")"
  if [[ ! -f "$BIBLE" ]]; then
    echo "error: 找不到圣经源 $BIBLE" >&2
    exit 1
  fi
fi

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

if [[ ! -d "$BACKEND/.venv" ]]; then
  python3 -m venv "$BACKEND/.venv"
fi
# shellcheck disable=SC1091
source "$BACKEND/.venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$BACKEND/requirements-build.txt"

cd "$BACKEND"
if [[ -n "$BIBLE" ]]; then
  python -m app.data.import_bible --source "$BIBLE"
else
  python -m app.data.import_bible
fi
python -m PyInstaller --noconfirm --clean lumina-backend.spec

cd "$FRONTEND"
if [[ -z "${APPLE_CERTIFICATE_BASE64:-}" ]]; then
  export CSC_IDENTITY_AUTO_DISCOVERY=false
fi
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run dist:mac
