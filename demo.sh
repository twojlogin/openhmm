#!/bin/bash
# demo.sh — uniwersalna nagrywarka demo.gif (X11 + ffmpeg).
# Podepniesz pod cokolwiek: dashboard, apkę, terminal.
#
# Użycie:
#   ./demo.sh                                   # domyślnie: stawia ./dashboard i nagrywa go
#   ./demo.sh -u http://127.0.0.1:8000 -t 15    # nagraj gotowy adres 15 s do demo.gif
#   ./demo.sh -c "./moja_apka" -u http://localhost:3000 -o apka.gif -t 30
#   ./demo.sh -t 10 -o pulpit.gif               # sam pulpit 10 s, nic nie stawiaj
#
# Flagi: -u URL (otwórz w przeglądarce)  -c CMD (odpal w tle przed nagraniem)
#        -t SEK (domyślnie 20)  -o PLIK (domyślnie demo.gif)  -g GEOM (domyślnie cały ekran)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
URL=""; CMD=""; TIME=20; OUT="$ROOT/demo.gif"; GEOM=""

while getopts "u:c:t:o:g:h" f; do
  case "$f" in
    u) URL="$OPTARG" ;;
    c) CMD="$OPTARG" ;;
    t) TIME="$OPTARG" ;;
    o) OUT="$OPTARG" ;;
    g) GEOM="$OPTARG" ;;
    h) sed -n '2,12p' "$0"; exit 0 ;;
  esac
done

command -v ffmpeg >/dev/null || { echo "[!] Brak ffmpeg: sudo apt install ffmpeg"; exit 1; }
[ -n "$DISPLAY" ] || { echo "[!] To nagrywanie działa na X11."; exit 1; }

APP_PID=""
cleanup() { [ -n "$APP_PID" ] && kill "$APP_PID" 2>/dev/null || true; }
trap cleanup EXIT

# 1) tryb domyślny: stawiaj ./dashboard z tego repo
if [ -z "$CMD" ] && [ -z "$URL" ] && [ -x "$ROOT/dashboard" ]; then
  "$ROOT/dashboard" &>/tmp/ohdemo.log &
  APP_PID=$!
  sleep 4
  URL="$(grep -oE 'http://127.0.0.1:[0-9]+' /tmp/ohdemo.log | head -1)"
  [ -n "$URL" ] || { echo "[!] Dashboard nie wstał, patrz /tmp/ohdemo.log"; exit 1; }
fi

# 2) własna komenda w tle
if [ -n "$CMD" ]; then
  echo "[*] Odpalam: $CMD"
  bash -c "$CMD" &>/tmp/demo-app.log &
  APP_PID=$!
  sleep 3
fi

# 3) otwórz URL w przeglądarce
if [ -n "$URL" ]; then
  echo "[*] Otwieram: $URL"
  (xdg-open "$URL" 2>/dev/null || firefox "$URL" 2>/dev/null || google-chrome "$URL" 2>/dev/null) &
fi

echo "[*] Masz 5 s — ustaw okno..."
sleep 5

[ -z "$GEOM" ] && GEOM="$(xdpyinfo 2>/dev/null | grep dimensions | awk '{print $2}' || echo 1366x768)"
echo "[*] NAGRYWANIE $TIME s ($GEOM) — działaj! Co nagrywasz, to będzie na gifie."
ffmpeg -y -f x11grab -s "$GEOM" -i "$DISPLAY" -r 10 -t "$TIME" /tmp/demo-cap.mp4 2>/dev/null

echo "[*] Konwertuję do gifa..."
ffmpeg -y -i /tmp/demo-cap.mp4 -vf "fps=8,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "$OUT" 2>/dev/null
rm -f /tmp/demo-cap.mp4
echo "[+] Gotowe: $OUT ($(du -h "$OUT" | cut -f1)) — podgląd: xdg-open $OUT"
