import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('synced', ROOT / 'tools/check_synced_snapshot.py')
synced = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(synced)


class SyncedSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.base = ET.parse(ROOT / 'default.xml').getroot()
        for project in self.base.findall('project'):
            if project.get('path') != 'kernel-6.1':
                project.set('revision', 'a' * 40)
        self.actual = copy.deepcopy(self.base)
        self.actual.find("project[@path='kernel-6.1']").set('revision', 'b' * 40)

    def test_repo_may_omit_path_equal_to_name(self):
        project = self.actual.find("project[@path='kernel/configs']")
        self.assertEqual(project.get('path'), project.get('name'))
        project.attrib.pop('path')
        synced.verify(self.base, self.actual, 'b' * 40)

    def test_rejects_unrelated_revision_change(self):
        self.actual.find("project[@path='common']").set('revision', 'c' * 40)
        with self.assertRaises(ValueError):
            synced.verify(self.base, self.actual, 'b' * 40)

    def test_rejects_source_identity_change(self):
        self.actual.find("project[@path='common']").set('name', 'other/source')
        with self.assertRaises(ValueError):
            synced.verify(self.base, self.actual, 'b' * 40)

    def test_rejects_missing_project(self):
        self.actual.remove(self.actual.find('project'))
        with self.assertRaises(ValueError):
            synced.verify(self.base, self.actual, 'b' * 40)

    def test_rejects_linkfile_change(self):
        self.actual.find('project/linkfile').set('dest', 'other')
        with self.assertRaises(ValueError):
            synced.verify(self.base, self.actual, 'b' * 40)


if __name__ == '__main__':
    unittest.main()
