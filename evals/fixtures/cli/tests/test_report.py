import io
import os
import tempfile
import unittest

from tally.__main__ import main

CSV = """date,category,amount,note
2026-01-04,travel,182.50,Train
2026-01-09,software,49.00,Editor
2026-02-02,travel,240.00,Flight
"""


class ReportTest(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        handle.write(CSV)
        handle.close()
        self.path = handle.name
        self.addCleanup(os.unlink, self.path)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = main(list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_prints_totals_by_category_largest_first(self):
        code, out, _ = self.run_cli("report", self.path)
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "2026-01-04 to 2026-02-02")
        self.assertTrue(lines[4].startswith("travel"))
        self.assertTrue(lines[-1].startswith("total"))
        self.assertIn("471.50", lines[-1])

    def test_since_filters_older_entries(self):
        _, out, _ = self.run_cli("report", self.path, "--since", "2026-02-01")
        self.assertIn("240.00", out)
        self.assertNotIn("software", out)

    def test_missing_file_is_reported_without_a_traceback(self):
        code, out, err = self.run_cli("report", "/no/such/file.csv")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("tally: Cannot read"))


if __name__ == "__main__":
    unittest.main()
