import tempfile
import unittest
from pathlib import Path

from tools.csharp_commonality import (
    _normalized_lines,
    find_duplicate_blocks,
    find_repeated_literals,
    scan,
)

# an 8-content-line block (braces are structural and skipped by normalization)
BLOCK = "\n".join(f"var x{i} = Compute({i}) + Offset({i});" for i in range(8))


class NormalizeTests(unittest.TestCase):
    def test_drops_structural_and_blank(self):
        norm = _normalized_lines("class C\n{\n\n    int X = 1;\n}\n")
        self.assertEqual([n for _, n in norm], ["class C", "int X = 1;"])

    def test_collapses_whitespace(self):
        norm = _normalized_lines("   int    a   =   1 ;\n")
        self.assertEqual(norm[0][1], "int a = 1 ;")


class DuplicateBlockTests(unittest.TestCase):
    def test_block_duplicated_across_files(self):
        files = {"A.cs": BLOCK + "\n", "B.cs": "// header\n" + BLOCK + "\n"}
        groups = find_duplicate_blocks(files, window=8)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["count"], 2)
        self.assertEqual({f for f, _ in groups[0]["occurrences"]}, {"A.cs", "B.cs"})

    def test_no_block_when_below_window(self):
        small = "\n".join(f"a{i} = {i};" for i in range(4))
        self.assertEqual(find_duplicate_blocks({"A.cs": small, "B.cs": small}, window=8), [])

    def test_no_block_when_unique(self):
        files = {"A.cs": BLOCK, "B.cs": "\n".join(f"y{i} = Other({i});" for i in range(8))}
        self.assertEqual(find_duplicate_blocks(files, window=8), [])

    def test_duplicated_comment_not_counted(self):
        # identical text only inside comments -> scrubbed -> not a code duplicate
        commented = "\n".join(f"// {l}" for l in BLOCK.splitlines())
        self.assertEqual(find_duplicate_blocks({"A.cs": commented, "B.cs": commented}, window=8), [])

    def test_overlapping_windows_collapse_to_one_group(self):
        # a 10-line duplicated run should report as a single group, not 3 sliding windows
        run = "\n".join(f"step{i}(ctx, {i});" for i in range(10))
        groups = find_duplicate_blocks({"A.cs": run, "B.cs": run}, window=8)
        self.assertEqual(len(groups), 1)


class RepeatedLiteralTests(unittest.TestCase):
    def test_repeated_number_across_files(self):
        files = {
            "A.cs": "var t = Timeout(30000);",
            "B.cs": "Connect(30000);",
            "C.cs": "Wait(30000);",
        }
        lits = find_repeated_literals(files, min_occurrences=3)
        vals = {c["value"] for c in lits}
        self.assertIn("30000", vals)

    def test_trivial_numbers_excluded(self):
        files = {"A.cs": "a = 0; b = 1;", "B.cs": "c = 0; d = 1;", "C.cs": "e = 0;"}
        self.assertEqual(find_repeated_literals(files, min_occurrences=3), [])

    def test_single_digit_numbers_excluded_multidigit_kept(self):
        files = {
            "A.cs": "a = 5; t = 60;",
            "B.cs": "b = 5; u = 60;",
            "C.cs": "c = 5; v = 60;",
        }
        vals = {c["value"] for c in find_repeated_literals(files, min_occurrences=3)}
        self.assertIn("60", vals)       # 2-digit magic kept
        self.assertNotIn("5", vals)     # single-digit noise dropped

    def test_punctuation_only_block_not_duplicated(self):
        # lines that are just commas must not form a duplicate block
        commas = "\n".join("," for _ in range(10))
        self.assertEqual(find_duplicate_blocks({"A.cs": commas, "B.cs": commas}, window=8), [])

    def test_repeated_string_candidate(self):
        files = {
            "A.cs": 'throw new Exception("ERR_AUTH_REQUIRED");',
            "B.cs": 'Log("ERR_AUTH_REQUIRED");',
            "C.cs": 'return Fail("ERR_AUTH_REQUIRED");',
        }
        lits = find_repeated_literals(files, min_occurrences=3)
        self.assertTrue(any("ERR_AUTH_REQUIRED" in c["value"] for c in lits))

    def test_single_file_not_flagged(self):
        # needs >= 2 distinct files
        files = {"A.cs": "x=30000; y=30000; z=30000;"}
        self.assertEqual(find_repeated_literals(files, min_occurrences=3), [])

    def test_number_in_comment_not_counted(self):
        files = {"A.cs": "// retry after 30000 ms", "B.cs": "// also 30000", "C.cs": "// 30000 again"}
        self.assertEqual(find_repeated_literals(files, min_occurrences=3), [])


class ScanTests(unittest.TestCase):
    def test_scan_excludes_generated_and_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "A.cs").write_text(BLOCK, encoding="utf-8")
            (root / "Gen.g.cs").write_text(BLOCK, encoding="utf-8")
            tdir = root / "App.Tests"
            tdir.mkdir()
            (tdir / "BTests.cs").write_text(BLOCK, encoding="utf-8")
            result, scope = scan([root], root=root)
            self.assertEqual(scope.included_files, 1)
            self.assertEqual(scope.excluded_generated, 1)
            self.assertEqual(scope.excluded_tests, 1)
            self.assertEqual(result["duplicate_blocks"], [])  # only one real file -> no dup


if __name__ == "__main__":
    unittest.main()
