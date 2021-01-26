import unittest

import os

import cellcollective

cases = [
{"url": "https://cellcollective.org/#2329/apoptosis-network",
    "model_id": "2329",
    "version": 1},
{"url": "https://research.cellcollective.org/?dashboard=true#module/2698:1/hcc1954-breast-cell-line-longterm-erbb-network/1",
    "model_id": "2698",
    "version": "1"},
]

class TestURL(unittest.TestCase):
    def test_ids(self):
        for case in cases:
            mid = (case["model_id"], case["version"])
            self.assertEqual(cellcollective.id_from_url(case["url"]), mid)

    def test_load(self):
        for case in cases:
            model = cellcollective.load(case["url"], auto_persistent=True)
            model_id = case["model_id"]
            version = case["version"]
            expected_filename = f"cellcollective-{model_id}-{version}.sbml"
            self.assertTrue(os.path.isfile(expected_filename))
            os.unlink(expected_filename)

if __name__ == '__main__':
    unittest.main()
