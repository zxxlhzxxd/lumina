#!/usr/bin/env bash
# Build the macOS arm64 installer.
# Usage:
#   ./scripts/build-mac-arm64.sh
#   ./scripts/build-mac-arm64.sh --bible /path/to/custom.lumina-bible --bible-tag cuv1919
#   ./scripts/build-mac-arm64.sh --sign
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
BIBLE=""
BIBLE_TAG=""
SIGN=0

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
    --bible-tag)
      BIBLE_TAG="${2:-}"
      if [[ -z "$BIBLE_TAG" ]]; then
        echo "error: --bible-tag 需要一个圣经版本缩写" >&2
        exit 1
      fi
      shift 2
      ;;
    --sign)
      SIGN=1
      shift
      ;;
    --no-sign)
      SIGN=0
      shift
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

if [[ -n "$BIBLE_TAG" && ! "$BIBLE_TAG" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "error: 圣经版本缩写只能包含字母、数字、点、下划线和连字符" >&2
  exit 1
fi

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
if [[ "$SIGN" -eq 1 ]]; then
  echo "Apple Developer 签名已开启。"
else
  export CSC_IDENTITY_AUTO_DISCOVERY=false
  echo "跳过 Apple Developer 签名。"
fi
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run dist:mac

if [[ -n "$BIBLE_TAG" ]]; then
  release_dir="$FRONTEND/release"
  shopt -s nullglob
  for src in "$release_dir"/Lumina-*-mac-arm64.dmg "$release_dir"/Lumina-*-mac-arm64.dmg.blockmap; do
    [[ -f "$src" ]] || continue
    base="$(basename "$src")"
    if [[ "$base" == *.dmg.blockmap ]]; then
      dest="$release_dir/${base%.dmg.blockmap}-${BIBLE_TAG}.dmg.blockmap"
    else
      dest="$release_dir/${base%.dmg}-${BIBLE_TAG}.dmg"
    fi
    mv "$src" "$dest"
    echo "安装包已标记圣经版本: $dest"
  done
fi
