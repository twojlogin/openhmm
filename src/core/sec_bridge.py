#!/usr/bin/env python3
"""
sec_bridge.py — READ-ONLY mostek do security-rocket.
NIC nie zmienia: wywołuje preflight_check.sh / system_check.sh /
security_report.sh, łapie stdout+stderr z timeoutem, zwraca tekst.
Skrypty modyfikujące (oneclick_harden.sh, ufw_manager.sh) są CELowo
niedostępne z tego mostka — hardening tylko ręcznie w terminalu.
"""
import os
import subprocess

# Katalog ze skryptami security-rocket (ten wskazany przez właściciela).
# Nadpisanie: OPENHMM_SEC_DIR=/inna/sciezka
SEC_DIR = os.environ.get(
    "OPENHMM_SEC_DIR",
    "/home/h5n1/Pulpit/katalog/projekty/00_SKRYPTOWNIA/security_rocket",
)

READONLY_SCRIPTS = {
    "preflight": "preflight_check.sh",
    "system": "system_check.sh",
    "report": "security_report.sh",
}

BLOCKED = ("oneclick_harden.sh", "ufw_manager.sh", "apply_and_verify.sh",
           "reinstall_core_components.sh")


def sec_dir_ok() -> bool:
    return os.path.isdir(SEC_DIR)


def run_check(name: str, timeout: int = 60) -> dict:
    """Uruchom jeden read-only check. Zwraca {name, ok, output}."""
    if name in BLOCKED or name not in READONLY_SCRIPTS:
        return {"name": name, "ok": False,
                "output": "BLOKADA: ten skrypt zmienia system — uruchom go ręcznie w terminalu."}
    script = os.path.join(SEC_DIR, READONLY_SCRIPTS[name])
    if not os.path.exists(script):
        return {"name": name, "ok": False,
                "output": f"Brak skryptu: {script} (ustaw OPENHMM_SEC_DIR jeśli masz go gdzie indziej)."}
    try:
        r = subprocess.run(["bash", script], capture_output=True, text=True,
                           timeout=timeout, cwd=SEC_DIR)
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return {"name": name, "ok": r.returncode == 0,
                "output": out.strip()[:20000]}
    except subprocess.TimeoutExpired:
        return {"name": name, "ok": False,
                "output": f"Timeout po {timeout}s — skrypt się zawiesił, nic nie zmieniono."}
    except Exception as e:
        return {"name": name, "ok": False, "output": f"Błąd mostka: {e}"}


def run_all(timeout_each: int = 60) -> dict:
    return {k: run_check(k, timeout_each) for k in READONLY_SCRIPTS}


if __name__ == "__main__":
    import json
    print(json.dumps(run_all(), indent=2, ensure_ascii=False))
