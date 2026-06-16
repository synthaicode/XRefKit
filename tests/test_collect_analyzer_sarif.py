import unittest

from tools.collect_analyzer_sarif import build_command, collect


class BuildCommandTests(unittest.TestCase):
    def test_errorlog_uses_escaped_comma_and_v21(self):
        cmd = build_command("App.csproj", "out.sarif")
        joined = " ".join(cmd)
        # the comma MUST be %2c-escaped or MSBuild falls back to SARIF v1.0.0
        self.assertIn("-p:ErrorLog=out.sarif%2cversion=2.1", cmd)
        self.assertNotIn("out.sarif,version", joined)

    def test_enables_analyzers(self):
        cmd = build_command("App.csproj", "out.sarif")
        self.assertIn("-p:EnableNETAnalyzers=true", cmd)
        self.assertIn("-p:RunAnalyzersDuringBuild=true", cmd)

    def test_target_and_config(self):
        cmd = build_command("App.csproj", "out.sarif", config="Release")
        self.assertEqual(cmd[:3], ["dotnet", "build", "App.csproj"])
        self.assertIn("Release", cmd)
        self.assertIn("--no-incremental", cmd)

    def test_ruleset_appended_when_given(self):
        cmd = build_command("App.csproj", "out.sarif", ruleset="prof.ruleset")
        self.assertIn("-p:CodeAnalysisRuleSet=prof.ruleset", cmd)

    def test_no_ruleset_by_default(self):
        cmd = build_command("App.csproj", "out.sarif")
        self.assertFalse(any(c.startswith("-p:CodeAnalysisRuleSet=") for c in cmd))

    def test_extra_props(self):
        cmd = build_command("App.csproj", "out.sarif", extra_props={"Foo": "Bar"})
        self.assertIn("-p:Foo=Bar", cmd)


class CollectDryRunTests(unittest.TestCase):
    def test_dry_run_does_not_execute(self):
        result = collect("App.csproj", "out.sarif", run=False)
        self.assertFalse(result["ran"])
        self.assertEqual(result["sarif"], "out.sarif")
        self.assertNotIn("returncode", result)
        self.assertEqual(result["command"][:2], ["dotnet", "build"])


if __name__ == "__main__":
    unittest.main()
