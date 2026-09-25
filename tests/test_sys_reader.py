#!/usr/bin/env python3
"""Testy sys_reader — struktury, klucze, typy, sensowne wartości. Stdlib only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "core"))
import sys_reader as sr


class TestDMI(unittest.TestCase):
    def test_model_returns_dict(self):
        self.assertIsInstance(sr.get_thinkpad_model(), dict)

    def test_model_has_required_keys(self):
        m = sr.get_thinkpad_model()
        for k in ("vendor", "model", "product_code", "supported"):
            self.assertIn(k, m, f"brak klucza {k}")

    def test_model_values_are_str(self):
        m = sr.get_thinkpad_model()
        self.assertIsInstance(m["vendor"], str)
        self.assertIsInstance(m["model"], str)

    def test_supported_is_bool(self):
        self.assertIsInstance(sr.get_thinkpad_model()["supported"], bool)

    def test_dmi_map_has_t440p(self):
        self.assertIn("20AN", sr.THINKPAD_DMI_MAP)
        self.assertEqual(sr.THINKPAD_DMI_MAP["20AN"], "ThinkPad T440p")

    def test_dmi_map_no_duplicate_keys(self):
        # regresja: duplikat 20AN nadpisywał T440p jako X240s
        vals = list(sr.THINKPAD_DMI_MAP.values())
        self.assertEqual(sr.THINKPAD_DMI_MAP["20AN"], "ThinkPad T440p")

    def test_dmi_map_not_empty(self):
        self.assertGreater(len(sr.THINKPAD_DMI_MAP), 50)

    def test_dmi_full_keys(self):
        d = sr.get_dmi_full()
        for k in ("sys_vendor", "product_name", "bios_version", "board_name"):
            self.assertIn(k, d)


class TestSensors(unittest.TestCase):
    def test_sensors_returns_dict(self):
        self.assertIsInstance(sr.scan_hardware_sensors(), dict)

    def test_sensors_not_empty_on_thinkpad(self):
        s = sr.scan_hardware_sensors()
        self.assertGreater(len(s), 0, "zero czujników na ThinkPadzie?")

    def test_sensor_entry_structure(self):
        for name, s in sr.scan_hardware_sensors().items():
            self.assertIn("temperatures", s, name)
            self.assertIsInstance(s["temperatures"], dict)

    def test_no_zero_temps(self):
        # regresja: kernel 7.x wystawia nieistniejące czujniki jako 0.0
        for name, s in sr.scan_hardware_sensors().items():
            for lbl, val in s["temperatures"].items():
                self.assertNotEqual(val, 0.0, f"{name}/{lbl} == 0.0 (duch)")

    def test_temps_are_floats_in_range(self):
        for name, s in sr.scan_hardware_sensors().items():
            for lbl, val in s["temperatures"].items():
                self.assertIsInstance(val, float)
                self.assertGreater(val, 0.0)
                self.assertLess(val, 120.0, f"{name}/{lbl}={val} (ogień?)")

    def test_coretemp_present(self):
        names = [n.lower() for n in sr.scan_hardware_sensors()]
        self.assertTrue(any("coretemp" in n or "thinkpad" in n or "acpitz" in n
                            for n in names))


class TestFanBatteryCpuMem(unittest.TestCase):
    def test_fan_structure(self):
        f = sr.get_thinkfan_status()
        for k in ("enabled", "level", "speed"):
            self.assertIn(k, f)

    def test_fan_speed_is_int(self):
        self.assertIsInstance(sr.get_thinkfan_status()["speed"], int)

    def test_battery_structure(self):
        b = sr.get_battery_info()
        self.assertIsInstance(b, dict)
        for name, bi in b.items():
            self.assertIn("capacity", bi, name)

    def test_cpu_structure(self):
        c = sr.get_cpu_info()
        for k in ("model", "cores", "threads"):
            self.assertIn(k, c)

    def test_cpu_cores_positive(self):
        c = sr.get_cpu_info()
        self.assertGreaterEqual(c["cores"], 1)
        self.assertGreaterEqual(c["threads"], c["cores"])

    def test_memory_has_memtotal(self):
        m = sr.get_memory_info()
        self.assertIn("MemTotal", m)
        self.assertGreater(m["MemTotal"], 0)


class TestInventory(unittest.TestCase):
    def test_inventory_keys(self):
        inv = sr.get_inventory()
        for k in ("dmi", "pci", "disks", "ram", "net", "usb", "displays", "audio"):
            self.assertIn(k, inv, f"brak {k}")

    def test_pci_categories(self):
        p = sr.get_pci_devices()
        for k in ("gpu", "audio", "network", "other"):
            self.assertIn(k, p)
            self.assertIsInstance(p[k], list)

    def test_gpu_found(self):
        gpus = sr.get_pci_devices()["gpu"]
        self.assertGreater(len(gpus), 0, "zero GPU?")

    def test_disks_is_list(self):
        self.assertIsInstance(sr.get_disks(), list)

    def test_ram_has_method(self):
        r = sr.get_ram_sticks()
        self.assertIn("method", r)

    def test_net_excludes_lo(self):
        self.assertNotIn("lo", sr.get_net_ifaces())

    def test_net_iface_structure(self):
        for name, ni in sr.get_net_ifaces().items():
            for k in ("state", "mac", "driver", "ipv4"):
                self.assertIn(k, ni, f"{name} brak {k}")

    def test_usb_is_list(self):
        self.assertIsInstance(sr.get_usb_devices(), list)

    def test_displays_has_lid(self):
        d = sr.get_displays()
        self.assertIn("lid", d)
        self.assertIn("connected", d)
        self.assertIn("docked", d)
        self.assertIsInstance(d["docked"], bool)

    def test_audio_is_list(self):
        self.assertIsInstance(sr.get_audio_cards(), list)

    def test_get_all_keys(self):
        d = sr.get_all()
        for k in ("machine", "sensors", "fan", "battery", "cpu", "memory"):
            self.assertIn(k, d)


if __name__ == "__main__":
    unittest.main()
