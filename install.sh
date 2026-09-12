#!/bin/bash
# install.sh — instalator OpenHMM dla zwykłych użytkowników (Mint/Ubuntu/Debian/Fedora/Arch)
set -e
echo "[*] OpenHMM installer"
if command -v apt >/dev/null; then
  sudo apt update && sudo apt install -y python3 python3-pip python3-venv
elif command -v dnf >/dev/null; then
  sudo dnf install -y python3 python3-pip
elif command -v pacman >/dev/null; then
  sudo pacman -Sy --noconfirm python python-pip
fi
python3 -m venv .venv 2>/dev/null || true
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
chmod +x start.sh src/core/cli.py
echo "[+] Gotowe. Uruchom: ./start.sh  (potem http://localhost:5066)"
echo "    albo CLI: .venv/bin/python src/core/cli.py"
