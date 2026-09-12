#!/usr/bin/env python3
"""
distro.py — wykrywanie dystrybucji i podpowiedzi komend per-distro.
Czysty stdlib. OpenHMM działa wszędzie, ale komendy się różnią.
"""
import os

PKG_MANAGERS = {
    "apt": {"check": "apt", "install": "sudo apt install -y",
            "distros": ["ubuntu", "debian", "linuxmint", "pop", "zorin", "elementary", "kali", "mx", "antix"]},
    "dnf": {"check": "dnf", "install": "sudo dnf install -y",
            "distros": ["fedora", "rhel", "centos", "rocky", "almalinux", "nobara"]},
    "pacman": {"check": "pacman", "install": "sudo pacman -Sy --noconfirm",
               "distros": ["arch", "manjaro", "endeavouros", "garuda", "artix"]},
    "zypper": {"check": "zypper", "install": "sudo zypper install -y",
               "distros": ["opensuse-leap", "opensuse-tumbleweed", "sles"]},
    "apk": {"check": "apk", "install": "sudo apk add",
            "distros": ["alpine", "postmarketos"]},
    "eopkg": {"check": "eopkg", "install": "sudo eopkg install -y",
              "distros": ["solus"]},
    "xbps": {"check": "xbps-install", "install": "sudo xbps-install -y",
             "distros": ["void"]},
}

FIREWALLS = {
    "apt": "ufw (sudo ufw status)",
    "dnf": "firewalld (sudo firewall-cmd --state)",
    "pacman": "ufw lub firewalld — sprawdź co masz",
    "zypper": "firewalld (sudo firewall-cmd --state)",
    "apk": "iptables/awall",
    "eopkg": "firewalld",
    "xbps": "iptables/ufw",
}


def read_os_release() -> dict:
    info = {}
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    except Exception:
        pass
    return info


def detect() -> dict:
    info = read_os_release()
    distro_id = info.get("ID", "unknown").lower()
    like = info.get("ID_LIKE", "").lower()
    name = info.get("PRETTY_NAME", info.get("NAME", "Unknown Linux"))

    pm = None
    for key, val in PKG_MANAGERS.items():
        if distro_id in val["distros"] or any(d in like for d in val["distros"]):
            pm = key
            break
    if pm is None:  # fallback: wykryj po dostępnej komendzie
        import shutil
        for key, val in PKG_MANAGERS.items():
            if shutil.which(val["check"]):
                pm = key
                break
    pm = pm or "apt"

    return {
        "id": distro_id,
        "like": like,
        "name": name,
        "version": info.get("VERSION_ID", ""),
        "pkg_manager": pm,
        "install_cmd": PKG_MANAGERS[pm]["install"],
        "firewall": FIREWALLS.get(pm, "?"),
        "venv_pkg": {"apt": "python3-venv", "dnf": "python3-pip",
                     "pacman": "python-pip", "zypper": "python3-pip",
                     "apk": "py3-pip", "eopkg": "pip",
                     "xbps": "python3-pip"}.get(pm, "python3-venv"),
    }


BANNER = r"""
 ██████╗ ██████╗ ███████╗███╗   ██╗██╗  ██╗███╗   ███╗███╗   ███╗
██╔═══██╗██╔══██╗██╔════╝████╗  ██║██║  ██║████╗ ████║████╗ ████║
██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████║██╔████╔██║██╔████╔██║
██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║╚██╔╝██║██║╚██╔╝██║
╚██████╔╝██║     ███████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║
 ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝
        OpenHMM — ThinkPad Przychodnia / Doctor — by Arek (H5N1)
              PL domyślnie • EN on board
"""


if __name__ == "__main__":
    import json
    print(BANNER)
    print(json.dumps(detect(), indent=2, ensure_ascii=False))
