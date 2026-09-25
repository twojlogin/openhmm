#!/usr/bin/env python3
"""Nowa warstwa: regresja duplikatów DMI (AST, nie runtime) + health na mockach.

Stare testy są sprzętowo-zależne (padną poza ThinkPadem). Te tutaj mają
działać wszędzie: czyste funkcje + mocki + efemeryczny port dla API.
Stdlib only.
"""
import ast
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from unittest import mock

ROOT = os.path.join(os.path.dirname(__file__), "..")
CORE = os.path.join(ROOT, "src", "core")
SYS_READER_SRC = os.path.join(CORE, "sys_reader.py")
PY = os.path.join(ROOT, ".venv", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable

sys.path.insert(0, CORE)
import sys_reader as sr


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestDmiMapNoDuplicatesStatic(unittest.TestCase):
    """Prawdziwa regresja: dict w runtime NIE widzi duplikatów (cicho nadpisuje),
    więc trzeba parsować źródło przez AST. Stary test test_dmi_map_no_duplicate_keys
    tego nie łapał — 30 kolizji przeszło niezauważonych."""

    def test_ast_no_duplicate_keys(self):
        with open(SYS_READER_SRC, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        seen = {}
        dups = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if getattr(t, "id", "") == "THINKPAD_DMI_MAP" \
                            and isinstance(node.value, ast.Dict):
                        for k in node.value.keys:
                            if isinstance(k, ast.Constant):
                                if k.value in seen:
                                    dups.append(k.value)
                                seen[k.value] = k.lineno
        self.assertEqual(dups, [], f"duplikaty kluczy DMI: {dups}")

    def test_t440p_survived(self):
        self.assertEqual(sr.THINKPAD_DMI_MAP.get("20AN"), "ThinkPad T440p")

    def test_prefix_match_t440p(self):
        with mock.patch.object(sr, "read_dmi_file") as rd:
            rd.side_effect = lambda p: {
                "/sys/class/dmi/id/sys_vendor": "LENOVO",
                "/sys/class/dmi/id/product_name": "20ANCTO1WW",
                "/sys/class/dmi/id/product_version": "ThinkPad T440p",
                "/sys/class/dmi/id/board_name": "20ANCTO1WW",
                "/sys/class/dmi/id/board_version": "0B98401",
                "/sys/class/dmi/id/bios_version": "GLET96WW",
                "/sys/class/dmi/id/bios_date": "09/12/2017",
            }.get(p, "")
            m = sr.get_thinkpad_model()
        self.assertEqual(m["model"], "ThinkPad T440p")
        self.assertTrue(m["supported"])
        self.assertTrue(m["dmi_match"])


class TestCpuTemps(unittest.TestCase):
    SENS = {
        "coretemp": {"temperatures": {"Package id 0": 72.0, "Core 0": 68.0}},
        "iwlwifi_1": {"temperatures": {"temp1": 55.0}},  # ma NIE wchodzić do CPU
        "BAT0": {"temperatures": {"temp": 30.0}},
    }

    def test_picks_only_cpu_sensors(self):
        self.assertEqual(sorted(sr.cpu_temps(self.SENS)), [68.0, 72.0])

    def test_fallback_when_no_cpu_sensor(self):
        s = {"acpitz": {"temperatures": {"temp1": 61.0}}}
        self.assertEqual(sr.cpu_temps(s), [61.0])

    def test_empty(self):
        self.assertEqual(sr.cpu_temps({}), [])


class TestTempStatus(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(sr.temp_status(60.0), "ok")

    def test_warn_boundary(self):
        self.assertEqual(sr.temp_status(85.0), "warn")
        self.assertEqual(sr.temp_status(94.9), "warn")

    def test_crit_boundary(self):
        self.assertEqual(sr.temp_status(95.0), "crit")

    def test_unknown(self):
        self.assertEqual(sr.temp_status(None), "unknown")


class TestBatteryWear(unittest.TestCase):
    def test_half_worn(self):
        w = sr.battery_wear({"energy_full": 50.0, "energy_full_design": 100.0})
        self.assertEqual(w["wear_pct"], 50.0)
        self.assertEqual(w["health_pct"], 50.0)

    def test_missing_data(self):
        w = sr.battery_wear({})
        self.assertIsNone(w["wear_pct"])
        self.assertIsNone(w["health_pct"])

    def test_zero_design_no_crash(self):
        w = sr.battery_wear({"energy_full": 50.0, "energy_full_design": 0})
        self.assertIsNone(w["wear_pct"])


class TestAssessHealth(unittest.TestCase):
    def _data(self, **kw):
        d = {"sensors": {"coretemp": {"temperatures": {"Package id 0": 60.0}}},
             "fan": {"enabled": True, "level": "auto", "speed": 2500},
             "battery": {"BAT0": {"capacity": "80", "energy_full": 90.0,
                                  "energy_full_design": 100.0}}}
        d.update(kw)
        return d

    def test_all_ok(self):
        h = sr.assess_health(self._data())
        self.assertEqual(h["overall"], "ok")
        self.assertEqual(h["temp"], {"max": 60.0, "status": "ok"})

    def test_hot_cpu_warn(self):
        d = self._data()
        d["sensors"] = {"coretemp": {"temperatures": {"Package id 0": 90.0}}}
        h = sr.assess_health(d)
        self.assertEqual(h["overall"], "warn")
        self.assertEqual(h["temp"]["status"], "warn")

    def test_crit_temp_dominates(self):
        d = self._data()
        d["sensors"] = {"coretemp": {"temperatures": {"Package id 0": 99.0}}}
        self.assertEqual(sr.assess_health(d)["overall"], "crit")

    def test_dead_fan_warn(self):
        d = self._data(fan={"enabled": False, "level": "unknown", "speed": 0})
        h = sr.assess_health(d)
        self.assertEqual(h["fan"]["status"], "warn")
        self.assertEqual(h["overall"], "warn")

    def test_worn_battery_crit(self):
        d = self._data()
        d["battery"] = {"BAT0": {"capacity": "60", "energy_full": 50.0,
                                 "energy_full_design": 100.0}}
        h = sr.assess_health(d)
        self.assertEqual(h["batteries"]["BAT0"]["status"], "crit")
        self.assertEqual(h["overall"], "crit")
        self.assertEqual(h["worst_wear_pct"], 50.0)

    def test_no_battery_ok(self):
        self.assertEqual(sr.assess_health(self._data(battery={}))["overall"], "ok")

    def test_json_serializable(self):
        json.dumps(sr.assess_health(self._data()), ensure_ascii=False)


class TestCliCheckFlag(unittest.TestCase):
    def test_check_exit_code_in_range(self):
        r = subprocess.run([PY, os.path.join(CORE, "cli.py"), "--check"],
                           capture_output=True, text=True, timeout=60, cwd=CORE)
        self.assertIn(r.returncode, (0, 1, 2, 3), r.stdout[-500:])
        self.assertIn("CHECK:", r.stdout)

    def test_health_line_always_printed(self):
        r = subprocess.run([PY, os.path.join(CORE, "cli.py")],
                           capture_output=True, text=True, timeout=60, cwd=CORE)
        self.assertIn("HEALTH:", r.stdout)


class TestHealthApi(unittest.TestCase):
    def test_api_health(self):
        port = free_port()
        proc = subprocess.Popen(
            [PY, "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
             "--port", str(port)],
            cwd=CORE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(50):
                try:
                    urllib.request.urlopen(base + "/api/lang/pl", timeout=2)
                    break
                except Exception:
                    time.sleep(0.2)
            with urllib.request.urlopen(base + "/api/health", timeout=30) as r:
                self.assertEqual(r.status, 200)
                d = json.loads(r.read().decode("utf-8"))
            self.assertIn("overall", d)
            self.assertIn(d["overall"], ("ok", "warn", "crit", "unknown"))
            self.assertIn("temp", d)
            self.assertIn("batteries", d)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


class TestSerialRedaction(unittest.TestCase):
    def test_redact_masks(self):
        with mock.patch.object(sr, "read_dmi_file", return_value="SECRET123"):
            d = sr.get_dmi_full(redact=True)
        self.assertEqual(d["product_serial"], "***")
        self.assertEqual(d["product_uuid"], "***")
        self.assertEqual(d["board_serial"], "***")
        # reszta danych zostaje (maskujemy tylko wrażliwe)
        self.assertEqual(d["sys_vendor"], "SECRET123")

    def test_no_redact_keeps(self):
        with mock.patch.object(sr, "read_dmi_file", return_value="SECRET123"):
            d = sr.get_dmi_full(redact=False)
        self.assertEqual(d["product_serial"], "SECRET123")

    def test_inventory_redact_passthrough(self):
        with mock.patch.object(sr, "read_dmi_file", return_value="SECRET123"):
            inv = sr.get_inventory(redact=True)
        self.assertEqual(inv["dmi"]["product_serial"], "***")


if __name__ == "__main__":
    unittest.main()
