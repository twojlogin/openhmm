#!/bin/bash
# demo.sh — nagrywa demo.gif dashboardu (X11 + ffmpeg).
# Użycie: ./demo.sh  → masz 5 s na ustawienie okna, potem 20 s nagrania:
#   klikaj zakładki Sprzęt / Naprawa / Pomoc / Bezpieczeństwo, przełącz PL/EN.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/_ensure_env.sh" 2>/dev/null || true

command -v ffmpeg >/dev/null || { echo "[!] Brak ffmpeg: sudo apt install ffmpeg"; exit 1; }
[ "$XDG_SESSION_TYPE" = "x11" ] || [ -n "$DISPLAY" ] || { echo "[!] To nagrywanie działa na X11."; exit 1; }

# 1) dashboard w tle (z obsługą zajętego portu)
"$ROOT/dashboard" &>/tmp/ohdemo.log &
DASH_PID=$!
sleep 4
URL="$(grep -oE 'http://127.0.0.1:[0-9]+' /tmp/ohdemo.log | head -1)"
[ -n "$URL" ] || { echo "[!] Dashboard nie wstał, patrz /tmp/ohdemo.log"; kill $DASH_PID; exit 1; }

# 2) otwórz w przeglądarce
(xdg-open "$URL" 2>/dev/null || firefox "$URL" 2>/dev/null || google-chrome "$URL" 2>/dev/null) &
echo "[*] Dashboard: $URL"
echo "[*] Masz 5 s — ustaw okno przeglądarki na wierzchu..."
sleep 5

# 3) nagrywanie pełnego ekranu 20 s
GEOM="$(xdpyinfo 2>/dev/null | grep dimensions | awk '{print $2}' || echo 1366x768)"
echo "[*] NAGRYWANIE 20 s — klikaj zakładki! (geometria $GEOM)"
ffmpeg -y -f x11grab -s "$GEOM" -i "$DISPLAY" -r 10 -t 20 /tmp/ohdemo.mp4 2>/dev/null
kill $DASH_PID 2>/dev/null || true

# 4) mp4 → gif (mały, do README)
ffmpeg -y -i /tmp/ohdemo.mp4 -vf "fps=8,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "$ROOT/demo.gif" 2>/dev/null
echo "[+] Gotowe: $ROOT/demo.gif ($(du -h "$ROOT/demo.gif" | cut -f1))"
echo "    Podgląd: xdg-open $ROOT/demo.gif"
