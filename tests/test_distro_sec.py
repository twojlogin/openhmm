#!/usr/bin/env python3
"""Testy distro + sec_bridge. Stdlib only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "core"))
import distro
import sec_bridge


class TestDistro(unittest.TestCase):
    def test_detect_returns_dict(self):
        self.assertIsInstance(distro.detect(), dict)

    def test_detect_has_keys(self):
        d = distro.detect()
        for k in ("id", "name", "pkg_manager", "install_cmd", "firewall"):
            self.assertIn(k, d, f"brak {k}")

    def test_pkg_manager_known(self):
        d = distro.detect()
        self.assertIn(d["pkg_manager"], distro.PKG_MANAGERS)

    def test_install_cmd_nonempty(self):
        self.assertTrue(distro.detect()["install_cmd"])

    def test_banner_nonempty(self):
        self.assertGreater(len(distro.BANNER.strip()), 100)

    def test_banner_mentions_openhmm(self):
        self.assertIn("OpenHMM", distro.BANNER)

    def test_firewall_hint_nonempty(self):
        self.assertTrue(distro.detect()["firewall"])

    def test_read_os_release(self):
        info = distro.read_os_release()
        self.assertIsInstance(info, dict)
        self.assertIn("ID", info)


class TestSecBridge(unittest.TestCase):
    def test_sec_dir_configured(self):
        self.assertTrue(sec_bridge.SEC_DIR)

    def test_blocked_oneclick(self):
        r = sec_bridge.run_check("oneclick_harden.sh")
        self.assertFalse(r["ok"])
        self.assertIn("BLOKADA", r["output"])

    def test_blocked_ufw(self):
        r = sec_bridge.run_check("ufw_manager.sh")
        self.assertFalse(r["ok"])

    def test_blocked_apply(self):
        r = sec_bridge.run_check("apply_and_verify.sh")
        self.assertFalse(r["ok"])

    def test_unknown_script_blocked(self):
        r = sec_bridge.run_check("rm_rf_everything.sh")
        self.assertFalse(r["ok"])

    def test_result_structure(self):
        r = sec_bridge.run_check("definitely-not-here.sh")
        for k in ("name", "ok", "output"):
            self.assertIn(k, r)

    def test_run_all_keys(self):
        d = sec_bridge.run_all(timeout_each=5)
        # run_all zwraca tylko read-only skrypty, nigdy modyfikujące
        for k in d:
            self.assertIn(k, ("preflight", "system", "report"))

    def test_run_all_values_have_output(self):
        d = sec_bridge.run_all(timeout_each=5)
        for k, v in d.items():
            self.assertIn("output", v, k)
            self.assertIsInstance(v["output"], str)


if __name__ == "__main__":
    unittest.main()
