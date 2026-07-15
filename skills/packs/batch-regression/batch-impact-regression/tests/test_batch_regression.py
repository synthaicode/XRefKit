import json, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from batch_regression import generate_candidates, normalize, compare, select_regression_set, summarize, analyze_paths
from code_tables import extract_source_tables, pairwise_table

class BatchRegressionTests(unittest.TestCase):
    def setUp(self):
        self.config = {"combination": {"elements": [{"name":"a","values":[1,2]}, {"name":"b","values":["x","y"]}], "constraints": [{"id":"ban","kind":"forbidden","when":{"all":[{"field":"a","op":"eq","value":2},{"field":"b","op":"eq","value":"y"}]},"evidence":["fixture"]}]}, "comparison": {"key_fields":["a","b"],"fields":["status","result","updated_rows"],"ignore_fields":["execution_id"],"normalize_fields":{"started_at":"datetime"}}, "planned_differences":[{"id":"new-rule","when":{"all":[{"field":"a","op":"eq","value":1},{"field":"b","op":"eq","value":"y"}]},"fields":["result"],"relation":"new requirement"}], "regression_set":{"max_size":10,"seed":4}}
    def test_generation_and_constraint(self):
        r = generate_candidates(self.config); self.assertEqual(r["all_candidate_count"], 4); self.assertEqual(r["post_constraint_count"], 3); self.assertEqual(sum(x["classification"] == "business_invalid" for x in r["classifications"]), 1)
    def test_conditional_and_unknown_predicates(self):
        self.assertTrue(self.config["planned_differences"][0]["when"]["all"])
        self.config["combination"]["constraints"].append({"id":"required","kind":"uncertain","when":{"all":[{"field":"a","op":"eq","value":2}]}})
        self.assertEqual(generate_candidates(self.config)["post_constraint_count"], 2)
        self.config["combination"]["constraints"].append({"id":"unknown","kind":"uncertain","when":{"all":[{"field":"a","op":"eq","value":1}]}})
        self.assertEqual(sum(x["classification"] == "uncertain" for x in generate_candidates(self.config)["classifications"]), 3)

    def test_csharp_sp_child_and_dynamic_sql_trace(self):
        trace = analyze_paths([{"id":"dual","csharp":["Batch.Run"],"stored_procedures":["dbo.Parent"],"child_stored_procedures":["dbo.Child"],"dynamic_sql":True}])
        self.assertEqual(trace["dual_layer_paths"], 1); self.assertEqual(trace["child_sp_paths"], 1); self.assertEqual(len(trace["dynamic_unknowns"]), 1)

    def test_extract_decision_and_pairwise_tables_from_csharp_and_sql(self):
        root = Path(__file__).parents[1] / "fixtures"
        extracted = extract_source_tables(root)
        self.assertIn("sample_batch.cs", extracted["files"]); self.assertIn("sample_batch.sql", extracted["files"])
        self.assertGreaterEqual(len(extracted["decision_table"]), 3)
        names = {factor["name"] for factor in extracted["factors"]}
        self.assertIn("kind", names); self.assertIn("amount", names)
        self.assertIn("A", next(f for f in extracted["factors"] if f["name"] == "kind")["values"])
        table = pairwise_table(extracted["factors"])
        self.assertEqual(table["uncovered_pairs"], []); self.assertGreater(len(table["rows"]), 0)
    def test_normalization_and_planned_vs_unexplained(self):
        old = [{"input":{"a":1,"b":"x"},"status":"success","result":10,"updated_rows":1,"execution_id":"old","started_at":"2026-01-01T00:00:00Z"},{"input":{"a":1,"b":"y"},"status":"success","result":10,"updated_rows":1}]
        new = [{"input":{"a":1,"b":"x"},"status":"success","result":10,"updated_rows":1,"execution_id":"new","started_at":"2026-01-01T00:01:00+00:00"},{"input":{"a":1,"b":"y"},"status":"success","result":11,"updated_rows":1}]
        rows = compare(old,new,self.config); self.assertEqual(rows[0]["classification"], "baseline_match"); self.assertEqual(rows[1]["classification"], "planned_difference")
        self.config["planned_differences"] = []; self.assertEqual(compare(old,new,self.config)[1]["classification"], "unexplained_difference")
    def test_errors_row_counts_paths_and_reproducible_set(self):
        old = [{"input":{"a":1,"b":"x"},"status":"success","result":1,"updated_rows":1,"path_refs":["csharp-sp-child"]}]
        new = [{"input":{"a":1,"b":"x"},"status":"system_error","error":{"code":"timeout"},"updated_rows":0,"path_refs":["csharp-sp-child"]}]
        rows = compare(old,new,self.config); self.assertEqual(rows[0]["classification"], "system_error"); self.assertEqual(select_regression_set(rows,self.config), select_regression_set(rows,self.config)); summary = summarize(generate_candidates(self.config),rows,self.config); self.assertEqual(summary["system_error"],1); self.assertEqual(summary["current_normal_count"],1); self.assertEqual(summary["business_error_count"],0); self.assertEqual(summary["new_system_error_count"],1)

if __name__ == "__main__": unittest.main()
