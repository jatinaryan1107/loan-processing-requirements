#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

port=8000
check_only=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --port)
      if [ "$#" -lt 2 ]; then
        echo 'Missing port. Usage: sh start.sh [--port 8000] [--check]' >&2
        exit 1
      fi
      port=$2
      shift 2
      ;;
    --check) check_only=true; shift ;;
    *) echo 'Usage: sh start.sh [--port 8000] [--check]' >&2; exit 1 ;;
  esac
done
case "$port" in
  ''|*[!0-9]*) echo 'Port must be a number from 1024 to 65535.' >&2; exit 1 ;;
esac
if [ "${#port}" -gt 5 ] || [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
  echo 'Port must be a number from 1024 to 65535.' >&2
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo 'Python environment missing. Run: python3 -m venv .venv' >&2
  echo 'Then: .venv/bin/python -m pip install -r requirements-lock.txt' >&2
  exit 1
fi
if ! .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo 'Python 3.11 or newer is required. Recreate the virtual environment with a supported Python version.' >&2
  exit 1
fi
if ! .venv/bin/python -c 'import chromadb, fastapi, uvicorn, dotenv, multipart, docx, pypdf, httpx'; then
  echo 'Python dependencies are incomplete. Run: .venv/bin/python -m pip install -r requirements-lock.txt' >&2
  exit 1
fi
if [ ! -f frontend/dist/index.html ]; then
  echo 'Built interface missing. Run: cd frontend && npm ci && npm run build && cd ..' >&2
  exit 1
fi
echo "Local workspace: http://127.0.0.1:$port"
if [ "$check_only" = true ]; then
  echo 'Startup checks passed. The server was not started.'
  exit 0
fi
echo 'Press Ctrl+C to stop. Saved projects remain in the configured SQLite database.'
exec .venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port "$port"
