#!/bin/bash
# _ensure_env.sh — wspólny bootstrap OpenHMM. Sourcing, nie uruchamianie directly.
# Sprawdza pythona >=3.10, stawia .venv, instaluje requirements. Idempotentny.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

need_python() {
  if ! command -v python3 >/dev/null 2>&1; then return 0; fi
  python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null || return 0
  return 1
}

if need_python; then
  echo "[*] Brak python3>=3.10, próbuję doinstalować..."
  if command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python python-pip
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y python3 python3-pip
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add python3 py3-pip py3-venv
  elif command -v eopkg >/dev/null 2>&1; then
    sudo eopkg install -y python3 pip
  elif command -v xbps-install >/dev/null 2>&1; then
    sudo xbps-install -y python3 pip
  else
    echo "[!] Nie znam Twojego menedżera pakietów. Zainstaluj ręcznie Python>=3.10 + venv/pip i wróć."; exit 1
  fi
fi

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "[*] Tworzę środowisko .venv..."
  python3 -m venv "$ROOT/.venv" || { echo "[!] venv się nie utworzył — doinstaluj python3-venv"; exit 1; }
fi

if [ -f "$ROOT/requirements.txt" ]; then
  # instaluj tylko gdy brak fastapi/uvicorn albo requirements nowsze niż marker
  MARK="$ROOT/.venv/.req_installed"
  if [ ! -f "$MARK" ] || [ "$ROOT/requirements.txt" -nt "$MARK" ] || ! "$ROOT/.venv/bin/python" -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "[*] Instaluję zależności..."
    "$ROOT/.venv/bin/pip" install -q --upgrade pip
    "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
    touch "$MARK"
  fi
fi

export OPENHMM_ROOT="$ROOT"
export OPENHMM_PY="$ROOT/.venv/bin/python"
