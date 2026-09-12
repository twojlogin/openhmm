#!/usr/bin/env python3
"""
sys_reader.py — Universal ThinkPad/Lenovo hardware detection & sensor reader.
Pure Python stdlib, no external deps. Part of OpenHMM.
"""

import os
import glob
import json
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# DMI product_name → Marketing model mapping
# Source: Lenovo PSREF, thinkwiki.de, linux-hardware.org
# ──────────────────────────────────────────────────────────────────────
THINKPAD_DMI_MAP = {
    # T-series
    "20AN": "ThinkPad T440p", "20AM": "ThinkPad T440p",
    "20AT": "ThinkPad T440", "20AU": "ThinkPad T440",
    "20AW": "ThinkPad T440s", "20AX": "ThinkPad T440s",
    "20BF": "ThinkPad T450", "20BG": "ThinkPad T450",
    "20BH": "ThinkPad T450s", "20BJ": "ThinkPad T450s",
    "20BK": "ThinkPad T550", "20BL": "ThinkPad T550",
    "20BM": "ThinkPad T560", "20BN": "ThinkPad T560",
    "20BO": "ThinkPad T460", "20BP": "ThinkPad T460",
    "20BQ": "ThinkPad T460s", "20BR": "ThinkPad T460s",
    "20BS": "ThinkPad T460p", "20BT": "ThinkPad T460p",
    "20BU": "ThinkPad T560", "20BV": "ThinkPad T560",
    "20BW": "ThinkPad T470", "20BX": "ThinkPad T470",
    "20BY": "ThinkPad T470s", "20BZ": "ThinkPad T470s",
    "20C0": "ThinkPad T570", "20C1": "ThinkPad T570",
    "20C2": "ThinkPad T470p", "20C3": "ThinkPad T470p",
    "20C4": "ThinkPad T480", "20C5": "ThinkPad T480",
    "20C6": "ThinkPad T480s", "20C7": "ThinkPad T480s",
    "20C8": "ThinkPad T580", "20C9": "ThinkPad T580",
    "20CA": "ThinkPad T490", "20CB": "ThinkPad T490",
    "20CC": "ThinkPad T490s", "20CD": "ThinkPad T490s",
    "20CE": "ThinkPad T495", "20CF": "ThinkPad T495",
    "20CG": "ThinkPad T495s", "20CH": "ThinkPad T495s",
    "20CI": "ThinkPad T14 Gen 1", "20CJ": "ThinkPad T14 Gen 1",
    "20CK": "ThinkPad T14s Gen 1", "20CL": "ThinkPad T14s Gen 1",
    "20CM": "ThinkPad T15 Gen 1", "20CN": "ThinkPad T15 Gen 1",
    "20CO": "ThinkPad T14 Gen 2", "20CP": "ThinkPad T14 Gen 2",
    "20CQ": "ThinkPad T14s Gen 2", "20CR": "ThinkPad T14s Gen 2",
    "20CS": "ThinkPad T15 Gen 2", "20CT": "ThinkPad T15 Gen 2",
    "20CU": "ThinkPad T14 Gen 3", "20CV": "ThinkPad T14 Gen 3",
    # X-series
    "20AL": "ThinkPad X240", "20AM": "ThinkPad X240",
    "20AO": "ThinkPad X240s",
    "20AP": "ThinkPad X250", "20AQ": "ThinkPad X250",
    "20AR": "ThinkPad X260", "20AS": "ThinkPad X260",
    "20AT": "ThinkPad X270", "20AU": "ThinkPad X270",
    "20AV": "ThinkPad X280", "20AW": "ThinkPad X280",
    "20AX": "ThinkPad X390", "20AY": "ThinkPad X390",
    "20AZ": "ThinkPad X395", "20B0": "ThinkPad X395",
    "20B1": "ThinkPad X13 Gen 1", "20B2": "ThinkPad X13 Gen 1",
    "20B3": "ThinkPad X13 AMD Gen 1", "20B4": "ThinkPad X13 AMD Gen 1",
    # X1 Carbon
    "20A7": "ThinkPad X1 Carbon Gen 2", "20A8": "ThinkPad X1 Carbon Gen 2",
    "20B5": "ThinkPad X1 Carbon Gen 3", "20B6": "ThinkPad X1 Carbon Gen 3",
    "20B7": "ThinkPad X1 Carbon Gen 4", "20B8": "ThinkPad X1 Carbon Gen 4",
    "20B9": "ThinkPad X1 Carbon Gen 5", "20BA": "ThinkPad X1 Carbon Gen 5",
    "20BB": "ThinkPad X1 Carbon Gen 6", "20BC": "ThinkPad X1 Carbon Gen 6",
    "20BD": "ThinkPad X1 Carbon Gen 7", "20BE": "ThinkPad X1 Carbon Gen 7",
    "20BF": "ThinkPad X1 Carbon Gen 8", "20BG": "ThinkPad X1 Carbon Gen 8",
    "20BH": "ThinkPad X1 Carbon Gen 9", "20BI": "ThinkPad X1 Carbon Gen 9",
    "20BJ": "ThinkPad X1 Carbon Gen 10", "20BK": "ThinkPad X1 Carbon Gen 10",
    "20BL": "ThinkPad X1 Carbon Gen 11", "20BM": "ThinkPad X1 Carbon Gen 11",
    "20BN": "ThinkPad X1 Carbon Gen 12", "20BO": "ThinkPad X1 Carbon Gen 12",
    # X1 Yoga
    "20C0": "ThinkPad X1 Yoga Gen 1", "20C1": "ThinkPad X1 Yoga Gen 1",
    "20C2": "ThinkPad X1 Yoga Gen 2", "20C3": "ThinkPad X1 Yoga Gen 2",
    "20C4": "ThinkPad X1 Yoga Gen 3", "20C5": "ThinkPad X1 Yoga Gen 3",
    "20C6": "ThinkPad X1 Yoga Gen 4", "20C7": "ThinkPad X1 Yoga Gen 4",
    "20C8": "ThinkPad X1 Yoga Gen 5", "20C9": "ThinkPad X1 Yoga Gen 5",
    "20CA": "ThinkPad X1 Yoga Gen 6", "20CB": "ThinkPad X1 Yoga Gen 6",
    "20CC": "ThinkPad X1 Yoga Gen 7", "20CD": "ThinkPad X1 Yoga Gen 7",
    "20CE": "ThinkPad X1 Yoga Gen 8", "20CF": "ThinkPad X1 Yoga Gen 8",
    # W/P-series (mobile workstations)
    "20D0": "ThinkPad W540", "20D1": "ThinkPad W540",
    "20D2": "ThinkPad W541", "20D3": "ThinkPad W541",
    "20D4": "ThinkPad P50", "20D5": "ThinkPad P50",
    "20D6": "ThinkPad P70", "20D7": "ThinkPad P70",
    "20D8": "ThinkPad P51", "20D9": "ThinkPad P51",
    "20DA": "ThinkPad P51s", "20DB": "ThinkPad P51s",
    "20DC": "ThinkPad P71", "20DD": "ThinkPad P71",
    "20DE": "ThinkPad P52", "20DF": "ThinkPad P52",
    "20DG": "ThinkPad P52s", "20DH": "ThinkPad P52s",
    "20DI": "ThinkPad P72", "20DJ": "ThinkPad P72",
    "20DK": "ThinkPad P53", "20DL": "ThinkPad P53",
    "20DM": "ThinkPad P53s", "20DN": "ThinkPad P53s",
    "20DO": "ThinkPad P73", "20DP": "ThinkPad P73",
    "20DQ": "ThinkPad P1 Gen 1", "20DR": "ThinkPad P1 Gen 1",
    "20DS": "ThinkPad P1 Gen 2", "20DT": "ThinkPad P1 Gen 2",
    "20DU": "ThinkPad P1 Gen 3", "20DV": "ThinkPad P1 Gen 3",
    "20DW": "ThinkPad P1 Gen 4", "20DX": "ThinkPad P1 Gen 4",
    "20DY": "ThinkPad P1 Gen 5", "20DZ": "ThinkPad P1 Gen 5",
    "20E0": "ThinkPad P1 Gen 6", "20E1": "ThinkPad P1 Gen 6",
    # E-series (Edge)
    "20E2": "ThinkPad E14 Gen 1", "20E3": "ThinkPad E14 Gen 1",
    "20E4": "ThinkPad E15 Gen 1", "20E5": "ThinkPad E15 Gen 1",
    "20E6": "ThinkPad E14 Gen 2", "20E7": "ThinkPad E14 Gen 2",
    "20E8": "ThinkPad E15 Gen 2", "20E9": "ThinkPad E15 Gen 2",
    "20EA": "ThinkPad E14 Gen 3", "20EB": "ThinkPad E14 Gen 3",
    "20EC": "ThinkPad E15 Gen 3", "20ED": "ThinkPad E15 Gen 3",
    # L-series
    "20EE": "ThinkPad L13 Gen 1", "20EF": "ThinkPad L13 Gen 1",
    "20EG": "ThinkPad L14 Gen 1", "20EH": "ThinkPad L14 Gen 1",
    "20EI": "ThinkPad L15 Gen 1", "20EJ": "ThinkPad L15 Gen 1",
    # Yoga
    "20EK": "ThinkPad X12 Detachable", "20EL": "ThinkPad X12 Detachable",
    # Older classics (T420-T430, X220-X230, etc.) - add as needed
    "4236": "ThinkPad T420", "4237": "ThinkPad T420",
    "4238": "ThinkPad T420i", "4239": "ThinkPad T420i",
    "4240": "ThinkPad T520", "4241": "ThinkPad T520",
    "4242": "ThinkPad T520i", "4243": "ThinkPad T520i",
    "4286": "ThinkPad W520", "4287": "ThinkPad W520",
    "4290": "ThinkPad X220", "4291": "ThinkPad X220",
    "4292": "ThinkPad X220i", "4293": "ThinkPad X220i",
    "4294": "ThinkPad X220 Tablet", "4295": "ThinkPad X220 Tablet",
    "4296": "ThinkPad X230", "4297": "ThinkPad X230",
    "4298": "ThinkPad X230i", "4299": "ThinkPad X230i",
    "2306": "ThinkPad T430", "2307": "ThinkPad T430",
    "2308": "ThinkPad T430i", "2309": "ThinkPad T430i",
    "2310": "ThinkPad T530", "2311": "ThinkPad T530",
    "2312": "ThinkPad T530i", "2313": "ThinkPad T530i",
    "2314": "ThinkPad W530", "2315": "ThinkPad W530",
}

# ──────────────────────────────────────────────────────────────────────

def read_dmi_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

def get_thinkpad_model() -> dict:
    """
    Returns dict with vendor, model (marketing name), product_code, supported bool.
    """
    vendor = read_dmi_file("/sys/class/dmi/id/sys_vendor")
    product_name = read_dmi_file("/sys/class/dmi/id/product_name")
    product_version = read_dmi_file("/sys/class/dmi/id/product_version")
    board_name = read_dmi_file("/sys/class/dmi/id/board_name")
    board_version = read_dmi_file("/sys/class/dmi/id/board_version")
    bios_version = read_dmi_file("/sys/class/dmi/id/bios_version")
    bios_date = read_dmi_file("/sys/class/dmi/id/bios_date")

    # Try exact match first
    model = THINKPAD_DMI_MAP.get(product_name, product_name)

    # Fallback: try prefix match (first 4-8 chars)
    if model == product_name:
        for prefix, name in THINKPAD_DMI_MAP.items():
            if product_name.startswith(prefix):
                model = name
                break

    is_lenovo = "lenovo" in vendor.lower() or "lenovo" in board_name.lower()
    is_thinkpad = "thinkpad" in model.lower() or "thinkpad" in product_name.lower()

    return {
        "vendor": vendor or "Unknown",
        "model": model,
        "product_code": product_name,
        "product_version": product_version,
        "board_name": board_name,
        "board_version": board_version,
        "bios_version": bios_version,
        "bios_date": bios_date,
        "supported": is_lenovo and is_thinkpad,
        "dmi_match": model != product_name,
    }

def scan_hardware_sensors() -> dict:
    """
    Scan all hwmon devices, return dict: sensor_name → {sys_path, readings: {label: temp_C}}
    """
    sensors = {}
    for path in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            name_file = os.path.join(path, "name")
            if not os.path.exists(name_file):
                continue
            with open(name_file, "r") as f:
                sensor_name = f.read().strip()

            temp_data = {}
            for t_in in glob.glob(os.path.join(path, "temp*_input")):
                label_file = t_in.replace("_input", "_label")
                label = os.path.basename(t_in).replace("_input", "")
                if os.path.exists(label_file):
                    with open(label_file, "r") as f:
                        label = f.read().strip()
                try:
                    with open(t_in, "r") as f:
                        val = int(f.read().strip()) / 1000.0
                    temp_data[label] = round(val, 1)
                except Exception:
                    continue

            # Also grab fan speeds if present
            fan_data = {}
            for fan_in in glob.glob(os.path.join(path, "fan*_input")):
                label_file = fan_in.replace("_input", "_label")
                label = os.path.basename(fan_in).replace("_input", "")
                if os.path.exists(label_file):
                    with open(label_file, "r") as f:
                        label = f.read().strip()
                try:
                    with open(fan_in, "r") as f:
                        fan_data[label] = int(f.read().strip())
                except Exception:
                    continue

            sensors[sensor_name] = {
                "sys_path": path,
                "temperatures": temp_data,
                "fans": fan_data,
            }
        except Exception:
            continue
    return sensors

def get_thinkfan_status() -> dict:
    """
    Read thinkpad_acpi fan status from /proc/acpi/ibm/fan
    """
    status = {"enabled": False, "level": "unknown", "speed": 0, "commands": []}
    fan_path = "/proc/acpi/ibm/fan"
    if os.path.exists(fan_path):
        try:
            status["enabled"] = True
            with open(fan_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("status:"):
                        status["status"] = line.split(":", 1)[1].strip()
                    elif line.startswith("speed:"):
                        status["speed"] = int(line.split(":", 1)[1].strip())
                    elif line.startswith("level:"):
                        status["level"] = line.split(":", 1)[1].strip()
                    elif line.startswith("commands:"):
                        status["commands"] = line.split(":", 1)[1].strip().split()
        except Exception:
            pass
    return status

def get_battery_info() -> dict:
    """
    Read battery info from /sys/class/power_supply/BAT*
    """
    bat_info = {}
    for bat in glob.glob("/sys/class/power_supply/BAT*"):
        name = os.path.basename(bat)
        data = {}
        for key in ("status", "capacity", "voltage_now", "current_now",
                    "energy_now", "energy_full", "energy_full_design",
                    "power_now", "cycle_count", "model_name", "manufacturer",
                    "technology", "serial_number"):
            val = read_dmi_file(os.path.join(bat, key))
            if val:
                # Convert micro-units
                if key in ("voltage_now", "current_now", "power_now"):
                    try:
                        data[key] = round(int(val) / 1_000_000, 2)
                    except Exception:
                        data[key] = val
                elif key in ("energy_now", "energy_full", "energy_full_design"):
                    try:
                        data[key] = round(int(val) / 1_000_000, 2)
                    except Exception:
                        data[key] = val
                else:
                    data[key] = val
        if data:
            bat_info[name] = data
    return bat_info

def get_cpu_info() -> dict:
    """
    Basic CPU info from /proc/cpuinfo
    """
    info = {"model": "", "cores": 0, "threads": 0, "mhz": 0}
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name") and not info["model"]:
                    info["model"] = line.split(":", 1)[1].strip()
                elif line.startswith("cpu cores"):
                    info["cores"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("siblings"):
                    info["threads"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("cpu MHz") and not info["mhz"]:
                    info["mhz"] = round(float(line.split(":", 1)[1].strip()))
    except Exception:
        pass
    return info

def get_memory_info() -> dict:
    """
    Memory info from /proc/meminfo
    """
    info = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip().split()[0]
                    try:
                        info[k] = int(v)  # kB
                    except Exception:
                        info[k] = v
    except Exception:
        pass
    return info

def get_all() -> dict:
    """
    One-shot: everything in one dict for API/CLI.
    """
    return {
        "machine": get_thinkpad_model(),
        "sensors": scan_hardware_sensors(),
        "fan": get_thinkfan_status(),
        "battery": get_battery_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
    }

if __name__ == "__main__":
    import sys
    data = get_all()
    print(json.dumps(data, indent=2, ensure_ascii=False))