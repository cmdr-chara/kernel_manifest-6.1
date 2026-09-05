import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify", ROOT / "tools/verify_manifest.py")
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.root = ET.parse(ROOT / "default.xml").getroot()

    def test_candidate(self):
        self.assertEqual(verify.validate(self.root), [])

    def test_rejects_moving_owned_ref(self):
        self.root.find("project[@path='kernel-6.1']").set("revision", "lineage-23.2")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_abandoned_owner(self):
        self.root.find("remote[@name='cmdr-chara']").set("fetch", "https://github.com/mt6878-devs/")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_missing_project(self):
        self.root.remove(self.root.find("project[@path='kernel-6.1']"))
        self.assertTrue(verify.validate(self.root))

    def test_rejects_duplicate_project(self):
        self.root.append(copy.deepcopy(self.root.find("project")))
        self.assertTrue(verify.validate(self.root))

    def test_rejects_broken_entry_point(self):
        self.root.find("project[@path='kernel_device_modules-6.1']/linkfile").set("src", "build.config.other")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_link_escape(self):
        self.root.find("project/linkfile").set("dest", "../outside")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_missing_upstream(self):
        self.root.find("project[@path='kernel-6.1']").attrib.pop("upstream")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_wrong_owner_repository(self):
        self.root.find("project[@path='kernel-6.1']").set("name", "unrelated")
        self.assertTrue(verify.validate(self.root))

    def test_rejects_unresolved_remote(self):
        self.root.find("project").set("remote", "missing")
        self.assertTrue(verify.validate(self.root))


if __name__ == "__main__":
    unittest.main()
