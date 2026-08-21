import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DevstackTests(unittest.TestCase):
    def test_seed_is_synthetic(self):
        data=json.loads((ROOT/'seed/synthetic_matter.json').read_text())
        self.assertFalse(data['contains_private_data'])
    def test_no_root_git(self):
        self.assertFalse((ROOT.parent/'.git').exists())
if __name__=='__main__': unittest.main()
