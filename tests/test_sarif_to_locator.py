import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from tools.sarif_to_locator import RULE_MAP, normalize


def _sarif(tool, results, version=None, sarif_version="2.1.0"):
    driver = {"name": tool}
    if version:
        driver["version"] = version
    return {"version": sarif_version, "runs": [{"tool": {"driver": driver}, "results": results}]}


def _result(rule_id, uri, line, col=1, level="warning"):
    return {
        "ruleId": rule_id,
        "level": level,
        "message": {"text": "diagnostic"},
        "locations": [
            {"physicalLocation": {"artifactLocation": {"uri": uri}, "region": {"startLine": line, "startColumn": col}}}
        ],
    }


def _write(tmp, obj, name="a.sarif"):
    p = Path(tmp) / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


class MappingTests(unittest.TestCase):
    def test_ca2200_maps_to_throw_rethrow(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("Microsoft.CodeAnalysis.NetAnalyzers", [_result("CA2200", "src/Foo.cs", 42, 13)]))
            hits, scope = normalize([sarif])
            self.assertEqual(len(hits), 1)
            h = hits[0]
            self.assertEqual(h.locator_id, "cs.err.throw_variable_rethrow")
            self.assertEqual(h.source_pattern_id, "130:throw-sites/variable-rethrow")
            self.assertEqual(h.external_rule_id, "CA2200")
            self.assertEqual((h.file, h.line, h.column), ("src/Foo.cs", 42, 13))
            self.assertTrue(h.detection_method.startswith("roslyn:"))

    def test_severity_is_dropped_and_candidate_set(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("csc", [_result("CA1849", "a.cs", 5, level="error")]))
            hits, _ = normalize([sarif])
            rec = asdict(hits[0])
            self.assertNotIn("level", rec)
            self.assertNotIn("severity", rec)
            self.assertEqual(rec["confidence"], "candidate")
            self.assertEqual(rec["judgment_status"], "unset")

    def test_ca1849_maps_to_sync_wait(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("NetAnalyzers", [_result("CA1849", "a.cs", 9)]))
            hits, _ = normalize([sarif])
            self.assertEqual(hits[0].locator_id, "cs.err.sync_wait_result")
            self.assertIn("GetAwaiter().GetResult()", hits[0].notes)

    def test_unmapped_rule_ignored_but_counted(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("X", [_result("CA9999", "a.cs", 1), _result("CA2200", "a.cs", 2)]))
            hits, scope = normalize([sarif])
            self.assertEqual([h.external_rule_id for h in hits], ["CA2200"])
            self.assertIn("CA9999", scope.unmapped_rule_ids)

    def test_empty_catch_rules_carry_signal_only_note(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("Sonar", [_result("S108", "a.cs", 3)]))
            hits, _ = normalize([sarif])
            self.assertEqual(hits[0].locator_id, "cs.err.empty_catch")
            self.assertIn("signal only", hits[0].notes)


class SarifVersionTests(unittest.TestCase):
    def test_v1_sarif_is_collection_error_not_no_hits(self):
        with tempfile.TemporaryDirectory() as d:
            # a v1 SARIF that actually contains a CA2200 hit must not be reported as 0
            sarif = _write(d, _sarif("csc", [_result("CA2200", "a.cs", 3)], sarif_version="1.0.0"))
            hits, scope = normalize([sarif])
            self.assertEqual(hits, [])
            self.assertTrue(any("unsupported SARIF version" in e for e in scope.collection_errors))

    def test_missing_version_is_collection_error(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("csc", [_result("CA2200", "a.cs", 3)], sarif_version=""))
            _, scope = normalize([sarif])
            self.assertTrue(any("unsupported SARIF version" in e for e in scope.collection_errors))

    def test_full_driver_name_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("Microsoft (R) Visual C# Compiler", [_result("CA2200", "a.cs", 3)]))
            hits, _ = normalize([sarif])
            self.assertEqual(hits[0].external_tool, "Microsoft (R) Visual C# Compiler")
            self.assertEqual(hits[0].detection_method, "roslyn:Microsoft (R) Visual C# Compiler")


class DedupTests(unittest.TestCase):
    def test_two_tools_same_location_merge_rule_ids(self):
        with tempfile.TemporaryDirectory() as d:
            s1 = _write(d, _sarif("NetAnalyzers", [_result("CA2200", "a.cs", 10, 5)]), "ca.sarif")
            s2 = _write(d, _sarif("SonarAnalyzer.CSharp", [_result("S3445", "a.cs", 10, 5)]), "sonar.sarif")
            hits, _ = normalize([s1, s2])
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].external_rule_id, "CA2200+S3445")

    def test_different_locations_not_merged(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("X", [_result("CA2200", "a.cs", 10), _result("CA2200", "a.cs", 20)]))
            hits, _ = normalize([sarif])
            self.assertEqual(len(hits), 2)


class ScopeTests(unittest.TestCase):
    def test_missing_sarif_file_is_collection_error(self):
        with tempfile.TemporaryDirectory() as d:
            hits, scope = normalize([Path(d) / "does-not-exist.sarif"])
            self.assertEqual(hits, [])
            self.assertEqual(len(scope.collection_errors), 1)

    def test_expected_tool_missing_is_collection_error_not_no_hits(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("Meziantou.Analyzer", [_result("MA0042", "a.cs", 1)]))
            hits, scope = normalize([sarif], expected_tools=["AsyncFixer"])
            self.assertEqual(len(hits), 1)  # candidate still produced
            self.assertTrue(any("AsyncFixer" in e for e in scope.collection_errors))

    def test_expected_tool_present_no_error(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("AsyncFixer", [_result("AsyncFixer02", "a.cs", 1)]))
            _, scope = normalize([sarif], expected_tools=["AsyncFixer"])
            self.assertEqual(scope.collection_errors, [])

    def test_result_without_location_counted(self):
        with tempfile.TemporaryDirectory() as d:
            bad = {"ruleId": "CA2200", "message": {"text": "no loc"}}
            sarif = _write(d, _sarif("X", [bad]))
            hits, scope = normalize([sarif])
            self.assertEqual(hits, [])
            self.assertEqual(scope.results_without_location, 1)

    def test_enabled_locators_derived_from_hits(self):
        with tempfile.TemporaryDirectory() as d:
            sarif = _write(d, _sarif("X", [_result("CA2200", "a.cs", 1), _result("AsyncFixer03", "a.cs", 2)]))
            _, scope = normalize([sarif])
            self.assertEqual(
                scope.enabled_locators,
                ["cs.err.async_void_non_event", "cs.err.throw_variable_rethrow"],
            )


class UriTests(unittest.TestCase):
    def test_file_uri_made_relative_to_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            uri = (root / "src" / "Foo.cs").as_uri()
            sarif = _write(d, _sarif("X", [_result("CA2200", uri, 7)]))
            hits, _ = normalize([sarif], root=root)
            self.assertEqual(hits[0].file, "src/Foo.cs")


class RuleMapTests(unittest.TestCase):
    def test_map_covers_first_batch_locators(self):
        locators = {m.locator_id for m in RULE_MAP.values()}
        self.assertEqual(
            locators,
            {
                "cs.err.throw_variable_rethrow",
                "cs.err.empty_catch",
                "cs.err.async_void_non_event",
                "cs.err.sync_wait_result",
                "cs.err.fire_and_forget",
            },
        )


if __name__ == "__main__":
    unittest.main()
