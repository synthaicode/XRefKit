import contextlib
import io
import json
import unittest

from fm.__main__ import main
from fm.gate import (
    EVAL_BLOCKED,
    EVAL_CLEAN,
    EVAL_NEEDS_REVIEW,
    aggregate,
    parse_unified_diff,
    run_evals,
)

SAMPLE_DIFF = """diff --git a/src/Auth/Login.cs b/src/Auth/Login.cs
index 111..222 100644
--- a/src/Auth/Login.cs
+++ b/src/Auth/Login.cs
@@ -10,3 +10,4 @@ public class Login
     public void Run()
     {
+        var conn = "Server=db;Database=x;User Id=sa;Password=Sup3rSecretValue;";
     }
diff --git a/tests/LoginTests.cs b/tests/LoginTests.cs
index 333..444 100644
--- a/tests/LoginTests.cs
+++ b/tests/LoginTests.cs
@@ -5,7 +5,7 @@ public class LoginTests
-    [Fact]
-    public void Login_Succeeds() { Assert.True(real); }
+    [Fact(Skip="flaky")]
+    public void Login_Succeeds() { Assert.True(true); }
diff --git a/db/Migrations/0007_add_col.sql b/db/Migrations/0007_add_col.sql
new file mode 100644
index 000..555
--- /dev/null
+++ b/db/Migrations/0007_add_col.sql
@@ -0,0 +1,1 @@
+ALTER TABLE users ADD COLUMN last_login timestamptz;
"""

CLEAN_DIFF = """diff --git a/src/Calc.cs b/src/Calc.cs
index 111..222 100644
--- a/src/Calc.cs
+++ b/src/Calc.cs
@@ -1,2 +1,3 @@
 public class Calc {
+    public int Add(int a, int b) => a + b;
 }
diff --git a/config/example.env b/config/example.env
index 333..444 100644
--- a/config/example.env
+++ b/config/example.env
@@ -1,1 +1,2 @@
 HOST=localhost
+API_KEY=your_api_key_here
"""


class GateTests(unittest.TestCase):
    def test_parse_tracks_paths_and_status(self):
        files = parse_unified_diff(SAMPLE_DIFF)
        by_path = {f.path: f for f in files}
        self.assertIn("src/Auth/Login.cs", by_path)
        self.assertEqual(by_path["db/Migrations/0007_add_col.sql"].status, "added")

    def test_added_line_numbers(self):
        files = parse_unified_diff(SAMPLE_DIFF)
        login = next(f for f in files if f.path == "src/Auth/Login.cs")
        # the added connection-string line is at new line 12
        self.assertTrue(any(no == 12 for no, _ in login.added))

    def test_all_checks_fire(self):
        files = parse_unified_diff(SAMPLE_DIFF)
        checks = {f.check for f in run_evals(files, scope=["src/auth/*", "tests/*"])}
        self.assertIn("test_removed", checks)
        self.assertIn("test_disabled", checks)
        self.assertIn("schema_migration", checks)
        self.assertIn("out_of_scope", checks)  # migration file is outside scope
        self.assertTrue(any(c.startswith("secret_leak") for c in checks))

    def test_secret_forces_blocked(self):
        files = parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual(aggregate(run_evals(files, scope=[])), EVAL_BLOCKED)

    def test_clean_diff_is_clean(self):
        files = parse_unified_diff(CLEAN_DIFF)
        findings = run_evals(files, scope=[])
        self.assertEqual(findings, [])
        self.assertEqual(aggregate(findings), EVAL_CLEAN)

    def test_placeholder_secret_not_flagged(self):
        files = parse_unified_diff(CLEAN_DIFF)
        self.assertFalse(any(f.check.startswith("secret_leak") for f in run_evals(files, scope=[])))

    def test_review_only_findings_aggregate_needs_review(self):
        diff = """diff --git a/tests/T.cs b/tests/T.cs
--- a/tests/T.cs
+++ b/tests/T.cs
@@ -1,2 +1,2 @@
-    [Fact]
+    [Fact(Skip="x")]
"""
        self.assertEqual(aggregate(run_evals(parse_unified_diff(diff), scope=[])), EVAL_NEEDS_REVIEW)

    def test_cli_blocked_exit_code(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            import tempfile
            import os

            fd, path = tempfile.mkstemp(suffix=".diff")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(SAMPLE_DIFF)
                rc = main(["gate", "eval", "--diff", path, "--json"])
            finally:
                os.remove(path)
        payload = json.loads(out.getvalue())
        self.assertEqual(rc, 1)
        self.assertEqual(payload["eval_verdict"], EVAL_BLOCKED)


if __name__ == "__main__":
    unittest.main()
