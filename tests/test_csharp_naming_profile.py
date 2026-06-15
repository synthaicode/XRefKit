import tempfile
import unittest
from pathlib import Path

from tools.csharp_naming_profile import (
    classify_casing,
    extract_text,
    profile_paths,
    _profile_kind,
    _parse_added_lines,
    changed_declarations,
    check_changed,
)


class CasingTests(unittest.TestCase):
    def test_pascal(self):
        self.assertEqual(classify_casing("OrderService"), "PascalCase")
        self.assertEqual(classify_casing("IOException"), "PascalCase")
        self.assertEqual(classify_casing("HtmlParser"), "PascalCase")

    def test_camel(self):
        self.assertEqual(classify_casing("getValue"), "camelCase")

    def test_underscore_camel(self):
        self.assertEqual(classify_casing("_buffer"), "_camelCase")

    def test_screaming(self):
        self.assertEqual(classify_casing("MAX_SIZE"), "SCREAMING_SNAKE")

    def test_other(self):
        self.assertEqual(classify_casing("weird_name"), "other")


def _extract(src):
    types, interfaces, methods, names = [], [], [], set()
    extract_text("F.cs", src, types, interfaces, methods, names)
    return types, interfaces, methods


class ExtractTests(unittest.TestCase):
    def test_class_record_struct(self):
        types, _, _ = _extract("public class Foo {}\nrecord Bar();\nstruct Baz {}\n")
        self.assertEqual({t[0] for t in types}, {"Foo", "Bar", "Baz"})

    def test_interface_with_line(self):
        _, ifaces, _ = _extract("public interface IRepository {}\n")
        self.assertEqual(ifaces[0][0], "IRepository")
        self.assertEqual(ifaces[0][2], 1)

    def test_method_requires_modifier(self):
        _, _, methods = _extract("public class C {\n public void DoWork() {}\n}\n")
        self.assertIn("DoWork", [m[0] for m in methods])

    def test_call_site_not_a_method(self):
        # calls inside a (modifier-bearing) method body must not be counted as declarations
        _, _, methods = _extract("public class C {\n public void Run() { Console.WriteLine(1); Helper(); }\n}\n")
        names = [m[0] for m in methods]
        self.assertIn("Run", names)
        self.assertNotIn("WriteLine", names)
        self.assertNotIn("Helper", names)

    def test_modifierless_method_is_missed_by_design(self):
        # documented limitation: a method with no access/decl modifier is not detected
        _, _, methods = _extract("class C {\n void Run() {}\n}\n")
        self.assertEqual([m[0] for m in methods], [])

    def test_constructor_excluded(self):
        _, _, methods = _extract("public class Widget {\n public Widget() {}\n public void Use() {}\n}\n")
        names = [m[0] for m in methods]
        self.assertIn("Use", names)
        self.assertNotIn("Widget", names)  # ctor name == type name

    def test_comment_and_string_not_matched(self):
        _, _, methods = _extract('public class C {\n // public void Ghost() {}\n var s = "public void Str() {}";\n public void Real() {}\n}\n')
        names = [m[0] for m in methods]
        self.assertEqual(names, ["Real"])

    def test_async_method_detected(self):
        _, _, methods = _extract("public class C {\n public async Task LoadAsync() {}\n}\n")
        self.assertIn("LoadAsync", [m[0] for m in methods])


class ProfileTests(unittest.TestCase):
    def test_interface_i_prefix_share(self):
        items = [("IFoo", "a.cs", 1), ("IBar", "a.cs", 2), ("Baz", "a.cs", 3)]
        p = _profile_kind("interface", items)
        self.assertAlmostEqual(p.affixes["I_prefix"]["share"], round(2 / 3, 3))

    def test_method_async_suffix_share(self):
        items = [("LoadAsync", "a.cs", 1), ("Save", "a.cs", 2)]
        p = _profile_kind("method", items)
        self.assertEqual(p.affixes["Async_suffix"]["count"], 1)

    def test_dominant_and_outliers(self):
        items = [("OrderService", "a.cs", 1), ("UserService", "a.cs", 2), ("legacy_thing", "a.cs", 9)]
        p = _profile_kind("type", items)
        self.assertEqual(p.dominant_casing, "PascalCase")
        self.assertEqual([o["name"] for o in p.outliers], ["legacy_thing"])

    def test_top_suffixes(self):
        items = [("AService", "a.cs", 1), ("BService", "a.cs", 2), ("CManager", "a.cs", 3)]
        p = _profile_kind("type", items)
        suffixes = dict(p.top_suffixes)
        self.assertEqual(suffixes.get("Service"), 2)
        self.assertEqual(suffixes.get("Manager"), 1)


class ProfilePathsTests(unittest.TestCase):
    def test_generated_and_tests_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Real.cs").write_text("public class Real {}\n", encoding="utf-8")
            (root / "Gen.g.cs").write_text("public class Gen {}\n", encoding="utf-8")
            tdir = root / "App.Tests"
            tdir.mkdir()
            (tdir / "FooTests.cs").write_text("public class FooTests {}\n", encoding="utf-8")
            profile, scope = profile_paths([root], root=root)
            self.assertEqual(profile["type"]["count"], 1)
            self.assertEqual(scope.excluded_generated, 1)
            self.assertEqual(scope.excluded_tests, 1)


class DeltaScopeTests(unittest.TestCase):
    def test_parse_added_lines(self):
        diff = (
            "diff --git a/Foo.cs b/Foo.cs\n"
            "--- a/Foo.cs\n"
            "+++ b/Foo.cs\n"
            "@@ -10,0 +11,2 @@\n"
            "+public class New {}\n"
            "+public class Two {}\n"
            "@@ -20 +22 @@\n"
            "+changed line\n"
        )
        added = _parse_added_lines(diff)
        self.assertEqual(added["Foo.cs"], {11, 12, 22})

    def test_parse_added_lines_ignores_deleted_file(self):
        diff = "--- a/Gone.cs\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-x\n-y\n"
        self.assertEqual(_parse_added_lines(diff), {})

    def test_changed_declarations_filters_to_added_lines(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Svc.cs").write_text(
                "public class Existing {}\npublic class Added {}\n", encoding="utf-8"
            )
            # only line 2 (Added) is in the diff
            decls = changed_declarations([root], {"Svc.cs": {2}}, root=root)
            names = [(k, n) for k, n, _, _ in decls]
            self.assertIn(("type", "Added"), names)
            self.assertNotIn(("type", "Existing"), names)

    def test_check_changed_flags_only_deviating_new_decl(self):
        profile = {
            "type": {"dominant_casing": "PascalCase", "affixes": {}},
            "interface": {"dominant_casing": "PascalCase", "affixes": {"I_prefix": {"share": 1.0}}},
        }
        decls = [
            ("type", "GoodService", "a.cs", 3),     # conforms
            ("type", "bad_name", "a.cs", 4),         # casing deviation
            ("interface", "Repository", "a.cs", 5),  # missing I prefix
            ("interface", "IRepository", "a.cs", 6), # conforms
        ]
        results = check_changed(profile, decls)
        deviations = {r["name"] for r in results if not r["conforms"]}
        self.assertEqual(deviations, {"bad_name", "Repository"})

    def test_check_changed_no_i_prefix_demand_when_share_low(self):
        profile = {"interface": {"dominant_casing": "PascalCase", "affixes": {"I_prefix": {"share": 0.4}}}}
        results = check_changed(profile, [("interface", "Repository", "a.cs", 1)])
        self.assertTrue(results[0]["conforms"])  # weak convention -> not enforced


if __name__ == "__main__":
    unittest.main()
