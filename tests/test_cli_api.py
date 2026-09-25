#!/usr/bin/env python3
"""Testy CLI (podprocesy) + API (żywy serwer + urllib). Stdlib only."""
import json
import os
import subprocess
import sys
import time
import unittest
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
CORE = os.path.join(ROOT, "src", "core")
PY = os.path.join(ROOT, ".venv", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable
CLI = os.path.join(CORE, "cli.py")


def run_cli(*args, timeout=60):
    return subprocess.run([PY, CLI, *args], capture_output=True, text=True,
                          timeout=timeout, cwd=CORE)


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self):
        r = run_cli("--help")
        self.assertEqual(r.returncode, 0)

    def test_help_lists_lang(self):
        r = run_cli("--help")
        self.assertIn("--lang", r.stdout)

    def test_default_pl(self):
        r = run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("ThinkPad", r.stdout)

    def test_lang_en(self):
        r = run_cli("--lang", "en")
        self.assertEqual(r.returncode, 0)
        self.assertIn("supported", r.stdout)

    def test_lang_pl(self):
        r = run_cli("--lang", "pl")
        self.assertEqual(r.returncode, 0)

    def test_banner_present(self):
        r = run_cli()
        self.assertIn("Przychodnia", r.stdout)

    def test_distro_line(self):
        r = run_cli()
        self.assertIn("Distro:", r.stdout)

    def test_json_valid(self):
        r = run_cli("--json")
        self.assertEqual(r.returncode, 0)
        start = r.stdout.find("{")
        self.assertGreaterEqual(start, 0)
        d = json.loads(r.stdout[start:])
        self.assertIn("machine", d)

    def test_full_flag(self):
        r = run_cli("--full", timeout=90)
        self.assertEqual(r.returncode, 0)
        self.assertIn("INWENTARYZACJA", r.stdout)

    def test_full_shows_gpu(self):
        r = run_cli("--full", timeout=90)
        self.assertIn("GPU:", r.stdout)

    def test_full_shows_net(self):
        r = run_cli("--full", timeout=90)
        self.assertIn("Sie", r.stdout)

    def test_sec_flag_runs(self):
        r = run_cli("--sec", timeout=180)
        self.assertEqual(r.returncode, 0)


class TestAPI(unittest.TestCase):
    BASE = "http://127.0.0.1:5066"
    proc = None

    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen(
            [PY, "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
             "--port", "5066"],
            cwd=CORE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                urllib.request.urlopen(cls.BASE + "/api/lang/pl", timeout=2)
                break
            except Exception:
                time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        if cls.proc:
            cls.proc.terminate()
            try:
                cls.proc.wait(timeout=5)
            except Exception:
                cls.proc.kill()

    def get(self, path, timeout=30):
        with urllib.request.urlopen(self.BASE + path, timeout=timeout) as r:
            self.assertEqual(r.status, 200, path)
            return json.loads(r.read().decode("utf-8"))

    def test_root_200(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            self.assertEqual(r.status, 200)
            html = r.read().decode("utf-8")
        self.assertIn("OpenHMM", html)

    def test_root_has_4_tabs(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        for tid in ('id="t1"', 'id="t2"', 'id="t3"', 'id="t4"'):
            self.assertIn(tid, html, tid)

    def test_root_has_tab_function(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        self.assertIn("function tab(", html)

    def test_root_no_store_header(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            cc = r.headers.get("Cache-Control", "")
        self.assertIn("no-store", cc)

    def test_root_has_lang_toggle(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        self.assertIn("toggleLang", html)

    def test_root_has_theme_toggle(self):
        with urllib.request.urlopen(self.BASE + "/", timeout=10) as r:
            html = r.read().decode("utf-8")
        self.assertIn("toggleTheme", html)

    def test_lang_pl_title(self):
        d = self.get("/api/lang/pl")
        self.assertIn("title", d)
        self.assertIn("Przychodnia", d["title"])

    def test_lang_en_title(self):
        d = self.get("/api/lang/en")
        self.assertIn("title", d)
        self.assertIn("Doctor", d["title"])

    def test_lang_pl_keys(self):
        d = self.get("/api/lang/pl")
        for k in ("tab_hardware", "tab_repair", "tab_help", "tab_security",
                  "device", "sensors", "fan", "battery"):
            self.assertIn(k, d, k)

    def test_lang_en_keys(self):
        d = self.get("/api/lang/en")
        for k in ("tab_hardware", "tab_repair", "tab_help", "tab_security"):
            self.assertIn(k, d, k)

    def test_lang_bad_fallback(self):
        d = self.get("/api/lang/xx")
        self.assertIn("title", d)

    def test_hardware_keys(self):
        d = self.get("/api/hardware")
        for k in ("machine", "sensors", "fan", "battery", "cpu", "memory",
                  "distro"):
            self.assertIn(k, d, k)

    def test_hardware_machine_supported(self):
        d = self.get("/api/hardware")
        self.assertIn("supported", d["machine"])
        self.assertIn("model", d["machine"])

    def test_hardware_fan(self):
        d = self.get("/api/hardware")
        self.assertIn("speed", d["fan"])

    def test_hardware_distro(self):
        d = self.get("/api/hardware")
        self.assertIn("pkg_manager", d["distro"])

    def test_fru_t440p(self):
        d = self.get("/api/fru/ThinkPad%20T440p")
        self.assertIn("parts", d)

    def test_fru_t440p_has_fan(self):
        d = self.get("/api/fru/ThinkPad%20T440p")
        self.assertIn("fan", d["parts"])

    def test_fru_unknown_model(self):
        d = self.get("/api/fru/NoSuchModelXYZ")
        self.assertTrue("error" in d or "models" in d)

    def test_readme_pl(self):
        d = self.get("/api/readme/pl")
        self.assertIn("content", d)
        self.assertIn("OpenHMM", d["content"])

    def test_readme_en(self):
        d = self.get("/api/readme/en")
        self.assertIn("content", d)

    def test_inventory_keys(self):
        d = self.get("/api/inventory", timeout=60)
        for k in ("dmi", "pci", "disks", "ram", "net", "usb", "displays",
                  "audio"):
            self.assertIn(k, d, k)

    def test_inventory_gpu(self):
        d = self.get("/api/inventory", timeout=60)
        self.assertGreater(len(d["pci"]["gpu"]), 0)

    def test_security_keys(self):
        d = self.get("/api/security", timeout=120)
        for k in ("preflight", "system", "report"):
            self.assertIn(k, d, k)

    def test_security_no_modifying_scripts(self):
        d = self.get("/api/security", timeout=120)
        for k in d:
            self.assertNotIn(k, ("oneclick", "ufw", "apply"))


if __name__ == "__main__":
    unittest.main()
