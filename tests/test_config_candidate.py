from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class ConfigCandidateTests(unittest.TestCase):
    def test_only_two_reviewed_extensions_over_kmi_candidate(self):
        root = ET.parse(ROOT / 'snapshots/2026-09-06-config-candidate.xml').getroot()
        self.assertEqual([e.tag for e in root], ['include', 'extend-project', 'extend-project'])
        self.assertEqual(root.find('include').get('name'), 'snapshots/2026-09-05-kmi-candidate.xml')
        expected = {
            'kernel_device_modules-6.1': ('android_kernel_device_modules', '034b70b1cbe1bb56f134bcb9d462daaec89aec7b', '1f98227e12a7bf94e5af8cc43501c0a4e376a422'),
            'build/bazel_mgk_rules': ('kernel-build-bazel_mgk_rules', 'd8ca975a69cedbfb9c24491fb5ef35ea4443498d', 'f955699182243b3bd9aa31b8938f33f8689cc8a1'),
        }
        actual = {p.get('path'): (p.get('name'), p.get('base-rev'), p.get('revision')) for p in root.findall('extend-project')}
        self.assertEqual(actual, expected)
        original = {p.get('path'): p for p in ET.parse(ROOT / 'default.xml').getroot().findall('project')}
        for path, (name, base, revision) in actual.items():
            self.assertEqual(original[path].get('name'), name)
            self.assertEqual(original[path].get('revision'), base)


if __name__ == '__main__':
    unittest.main()
