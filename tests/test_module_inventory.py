import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('inventory', Path(__file__).resolve().parents[1] / 'tools/compare_module_inventory.py')
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class ModuleInventoryTests(unittest.TestCase):
    def setUp(self):
        self.prebuilt = {'schema_version': 1, 'status': 'PASS', 'artifacts': [
            {'path': 'vendor_dlkm/a.ko', 'sha256': 'a' * 64, 'modinfo': {'vermagic': ['old']}},
            {'path': 'vendor_ramdisk/b.ko', 'sha256': 'b' * 64, 'modinfo': {'vermagic': ['older']}}]}

    def test_missing_modules_and_duplicate_outputs(self):
        result = inventory.compare('out/a.ko\t123\nstaging/a.ko\t24\n', self.prebuilt, {'boot': 'a.ko\nb.ko\nb.ko\n'})
        self.assertEqual(result['observed_source_module_names'], 1)
        self.assertEqual(result['prebuilt_names_not_observed'], ['b.ko'])
        self.assertEqual(result['load_lists']['boot']['not_observed'], ['b.ko'])
        self.assertEqual(result['load_lists']['boot']['entries'], 3)

    def test_complete_names_are_not_abi_approval(self):
        result = inventory.compare('a.ko\t12\nb.ko\t15\n', self.prebuilt, {})
        self.assertEqual(result['prebuilt_names_not_observed'], [])
        self.assertEqual(result['source_equivalence'], 'GAP')
        self.assertEqual(result['release_status'], 'BLOCKED')

    def test_reject_invalid_records(self):
        for text in ('a.ko\t-1', 'a.ko', 'a.ko\t1\textra', '../a.ko\t1', '/a.ko\t1', 'a//b.ko\t1'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                inventory.observed_names(text)

    def test_require_modules(self):
        with self.assertRaises(ValueError):
            inventory.observed_names('Image\t100')

    def test_reject_failed_prebuilt_evidence(self):
        self.prebuilt['status'] = 'FAIL'
        with self.assertRaises(ValueError):
            inventory.compare('a.ko\t1', self.prebuilt, {})

    def test_reject_duplicate_prebuilt_path(self):
        self.prebuilt['artifacts'].append(self.prebuilt['artifacts'][0])
        with self.assertRaises(ValueError):
            inventory.compare('a.ko\t1', self.prebuilt, {})

    def test_reject_missing_digest(self):
        self.prebuilt['artifacts'][0]['sha256'] = ''
        with self.assertRaises(ValueError):
            inventory.compare('a.ko\t1', self.prebuilt, {})

    def test_reject_bad_or_empty_load_list(self):
        for text in ('../a.ko', 'sub/a.ko', 'a.so', ''):
            with self.subTest(text=text), self.assertRaises(ValueError):
                inventory.compare('a.ko\t1', self.prebuilt, {'boot': text})


if __name__ == '__main__':
    unittest.main()
