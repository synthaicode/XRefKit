import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

from tools.error_policy_audit import aggregate, run


def _custom(file, line, locator="cs.err.empty_catch", col=5):
    return SimpleNamespace(
        file=file, line=line, column=col, locator_id=locator,
        source_pattern_id="130:catch-blocks/empty-catch", tier="T2",
        detection_method="python_scrub_block_heuristic",
        notes="empty catch body; no intentional marker in body", snippet="catch { }",
    )


def _analyzer(file, line, locator="cs.err.empty_catch", rule="RCS1075", col=7):
    return SimpleNamespace(
        file=file, line=line, column=col, locator_id=locator,
        source_pattern_id="130:catch-blocks/empty-catch", tier="T2",
        detection_method="roslyn:Roslynator", external_rule_id=rule,
        notes="signal only",
    )


class AggregateTests(unittest.TestCase):
    def test_custom_only(self):
        out = aggregate([_custom("A.cs", 3)], [])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["confidence"], "candidate")
        self.assertEqual(len(out[0]["sources"]), 1)
        self.assertIsNone(out[0]["sources"][0]["rule"])

    def test_analyzer_only(self):
        out = aggregate([], [_analyzer("A.cs", 3)])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["sources"][0]["rule"], "RCS1075")

    def test_corroboration_merges_same_file_line_locator(self):
        out = aggregate([_custom("A.cs", 3, col=5)], [_analyzer("A.cs", 3, col=7)])
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]["sources"]), 2)
        self.assertEqual(out[0]["column"], 5)  # min column across sources
        detectors = {s["detector"] for s in out[0]["sources"]}
        self.assertEqual(detectors, {"python_scrub_block_heuristic", "roslyn:Roslynator"})

    def test_different_line_not_merged(self):
        out = aggregate([_custom("A.cs", 3)], [_analyzer("A.cs", 9)])
        self.assertEqual(len(out), 2)

    def test_different_locator_not_merged(self):
        out = aggregate([], [_analyzer("A.cs", 3, locator="cs.err.empty_catch"),
                             _analyzer("A.cs", 3, locator="cs.err.sync_wait_result", rule="CA1849")])
        self.assertEqual(len(out), 2)

    def test_sorted_by_file_line(self):
        out = aggregate([_custom("B.cs", 1), _custom("A.cs", 9), _custom("A.cs", 2)], [])
        self.assertEqual([(c["file"], c["line"]) for c in out], [("A.cs", 2), ("A.cs", 9), ("B.cs", 1)])


def _sarif(rule, uri, line, col=1):
    return {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "Roslynator"}},
            "results": [{
                "ruleId": rule, "level": "warning", "message": {"text": "x"},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri},
                              "region": {"startLine": line, "startColumn": col}}}],
            }],
        }],
    }


class RunIntegrationTests(unittest.TestCase):
    def test_custom_and_analyzer_corroborate_real_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Svc.cs").write_text("void M() {\n try { F(); }\n catch (Exception) { }\n}\n", encoding="utf-8")
            sarif = root / "a.sarif"
            sarif.write_text(json.dumps(_sarif("RCS1075", "Svc.cs", 3)), encoding="utf-8")

            candidates, scope = run([str(root)], [str(sarif)], root=str(root))
            empties = [c for c in candidates if c["locator_id"] == "cs.err.empty_catch" and c["file"] == "Svc.cs" and c["line"] == 3]
            self.assertEqual(len(empties), 1)
            self.assertEqual(len(empties[0]["sources"]), 2)  # custom + RCS1075 corroborate
            self.assertEqual(scope["candidate_count"], len(candidates))

    def test_missing_sarif_surfaces_collection_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Svc.cs").write_text("catch (Exception) { }\n", encoding="utf-8")
            candidates, scope = run([str(root)], [str(root / "nope.sarif")], root=str(root))
            self.assertTrue(scope["collection_errors"])  # not silently dropped


if __name__ == "__main__":
    unittest.main()
