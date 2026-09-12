#!/usr/bin/env python3
"""Testy meta: słowniki, baza FRU, pliki projektu, serializacja. Stdlib only."""
import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "src", "data")
sys.path.insert(0, os.path.join(ROOT, "src", "core"))
import sys_reader as sr


class TestLangFiles(unittest.TestCase):
    def load(self, lang):
        with open(os.path.join(DATA, f"{lang}.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_pl_valid_json(self):
        self.assertIsInstance(self.load("pl"), dict)

    def test_en_valid_json(self):
        self.assertIsInstance(self.load("en"), dict)

    def test_lang_parity(self):
        # EN i PL muszą mieć te same klucze (przełącznik nie może sypać undefined)
        pl, en = self.load("pl"), self.load("en")
        self.assertEqual(set(pl.keys()), set(en.keys()))

    def test_lang_no_empty_values(self):
        for lang in ("pl", "en"):
            for k, v in self.load(lang).items():
                self.assertTrue(v, f"{lang}.{k} puste!")

    def test_lang_count(self):
        self.assertGreaterEqual(len(self.load("pl")), 20)


class TestFruDb(unittest.TestCase):
    def load(self):
        with open(os.path.join(DATA, "fru_db.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_db_valid(self):
        self.assertIsInstance(self.load(), dict)

    def test_has_t440p(self):
        self.assertIn("ThinkPad T440p", self.load())

    def test_model_structure(self):
        for model, data in self.load().items():
            self.assertIn("parts", data, model)
            self.assertIsInstance(data["parts"], dict)

    def test_part_structure(self):
        for model, data in self.load().items():
            for pname, p in data["parts"].items():
                self.assertIn("fru", p, f"{model}/{pname}")
                self.assertIn("desc_pl", p, f"{model}/{pname}")
                self.assertIn("steps", p, f"{model}/{pname}")
                self.assertIsInstance(p["steps"], list)
                self.assertGreater(len(p["steps"]), 0, f"{model}/{pname} bez kroków")

    def test_min_models(self):
        self.assertGreaterEqual(len(self.load()), 5)


class TestProjectFiles(unittest.TestCase):
    def test_requirements_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "requirements.txt")))

    def test_requirements_fastapi(self):
        txt = open(os.path.join(ROOT, "requirements.txt")).read().lower()
        self.assertIn("fastapi", txt)
        self.assertIn("uvicorn", txt)

    def test_readme_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "README.md")))

    def test_readme_mentions_demo(self):
        txt = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
        self.assertIn("demo", txt.lower())

    def test_license_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "LICENSE")))

    def test_status_executable(self):
        self.assertTrue(os.access(os.path.join(ROOT, "status"), os.X_OK))

    def test_dashboard_executable(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "dashboard")))

    def test_pyproject_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "pyproject.toml")))


class TestSerialization(unittest.TestCase):
    def test_get_all_json_serializable(self):
        d = sr.get_all()
        json.dumps(d, ensure_ascii=False)

    def test_inventory_json_serializable(self):
        json.dumps(sr.get_inventory(), ensure_ascii=False)

    def test_distro_json_serializable(self):
        import distro
        json.dumps(distro.detect(), ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
