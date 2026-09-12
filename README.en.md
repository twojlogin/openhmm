# OpenHMM — ThinkPad Doctor

Got an old ThinkPad running Linux (Mint / Ubuntu)? Start here.

**What it is:** free, local, offline panel that tells you what's wrong with your
machine — temps, fan, battery, model + FRU part numbers and repair steps.
No accounts, no telemetry, no cloud. Just Python + your hardware.

**3 commands:**
```bash
./install.sh   # once: sets up venv
./status       # terminal: ✅ / ⚠️ / ❌
./dashboard    # web: http://localhost:5066 (Hardware / Repair tabs)
```

Default language is **Polish** (this project is built by a Pole, for ThinkPad
users first). Switch: `./status --lang en` or the EN button in the dashboard.
Repair steps in `fru_db.json` are in Polish + link to the original Lenovo HMM PDF (EN).

> ⚠️ The separate hardening module (`security-rocket`) changes SSH/UFW — run
> `preflight_check.sh` first, keep physical access. The hardware dashboard
> (this folder) is read-only, changes nothing.
