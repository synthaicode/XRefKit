import tempfile
import unittest
from pathlib import Path

from tools.error_policy_locator import (
    _EMPTY_CATCH,
    _ENABLED_LOCATORS,
    _THROW_VARIABLE_RETHROW,
    _scrub,
    scan_paths,
    scan_text,
)


def _hits(src: str):
    return scan_text("Sample.cs", src, "scan-test")


def _hits_for(src: str, locator_id: str):
    return [h for h in _hits(src) if h.locator_id == locator_id]


class ScrubTests(unittest.TestCase):
    def test_scrub_preserves_length_and_newlines(self):
        src = 'a = "x";\nb = 2;\n'
        scrubbed = _scrub(src)
        self.assertEqual(len(scrubbed), len(src))
        self.assertEqual(scrubbed.count("\n"), src.count("\n"))

    def test_scrub_blanks_line_comment(self):
        self.assertNotIn("throw", _scrub("x; // throw ex;\n"))

    def test_scrub_blanks_block_comment(self):
        self.assertNotIn("throw", _scrub("/* throw ex; */ y;"))

    def test_scrub_blanks_string_literal(self):
        self.assertNotIn("throw", _scrub('var s = "throw ex;";'))

    def test_scrub_blanks_verbatim_string(self):
        self.assertNotIn("throw", _scrub('var s = @"throw ex; "" still";'))

    def test_scrub_blanks_raw_string(self):
        self.assertNotIn("throw", _scrub('var s = """throw ex;""";'))

    def test_scrub_blanks_interpolated_raw_string(self):
        self.assertNotIn("throw", _scrub('var s = $"""throw ex;""";'))

    def test_scrub_blanks_multi_dollar_raw_string(self):
        self.assertNotIn("throw", _scrub('var s = $$"""throw ex;""";'))


class ThrowVariableRethrowTests(unittest.TestCase):
    def test_true_positive(self):
        src = "try { F(); }\ncatch (Exception ex)\n{\n    throw ex;\n}\n"
        hits = _hits(src)
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.locator_id, _THROW_VARIABLE_RETHROW)
        self.assertEqual(h.line, 4)
        self.assertEqual(h.confidence, "candidate")
        self.assertEqual(h.judgment_status, "unset")
        self.assertEqual(h.source_pattern_id, "130:throw-sites/variable-rethrow")

    def test_bare_rethrow_not_matched(self):
        self.assertEqual(_hits("catch (Exception ex)\n{\n throw;\n}"), [])

    def test_throw_new_not_matched(self):
        src = "catch (Exception ex)\n{\n throw new InvalidOperationException();\n}"
        self.assertEqual(_hits(src), [])

    def test_throw_qualified_new_not_matched(self):
        src = "catch (Exception ex)\n{\n throw new Ns.CustomException();\n}"
        self.assertEqual(_hits(src), [])

    def test_comment_not_matched(self):
        # the throw locator ignores the commented rethrow (empty_catch may still fire)
        self.assertEqual(
            _hits_for("catch (Exception ex)\n{\n // throw ex;\n}", _THROW_VARIABLE_RETHROW), []
        )

    def test_string_not_matched(self):
        self.assertEqual(_hits('catch (Exception ex)\n{\n var s = "throw ex;";\n}'), [])

    def test_non_catch_variable_not_matched(self):
        # `local` is not the catch variable, so the rethrow is not flagged
        src = "catch (Exception ex)\n{\n var local = Build();\n throw local;\n}"
        self.assertEqual(_hits(src), [])

    def test_outside_catch_not_matched(self):
        src = "void M(Exception ex)\n{\n throw ex;\n}"
        self.assertEqual(_hits(src), [])

    def test_when_filter(self):
        src = "catch (Exception ex) when (ex.Message != null)\n{\n throw ex;\n}"
        hits = _hits(src)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].line, 3)

    def test_interpolated_raw_string_not_matched(self):
        src = 'catch (Exception ex)\n{\n var s = $"""throw ex;""";\n}'
        self.assertEqual(_hits(src), [])

    def test_catch_with_fully_qualified_type(self):
        src = "catch (System.Exception ex)\n{\n throw ex;\n}"
        self.assertEqual(len(_hits(src)), 1)

    def test_catch_with_array_type(self):
        src = "catch (MyException[] ex)\n{\n throw ex;\n}"
        self.assertEqual(len(_hits(src)), 1)

    def test_generic_catch_type(self):
        src = "catch (MyException<T> ex)\n{\n throw ex;\n}"
        hits = _hits(src)
        self.assertEqual(len(hits), 1)

    def test_multiline_throw(self):
        # `throw ex ;` split across lines still tokenizes
        src = "catch (Exception ex)\n{\n throw\n   ex;\n}"
        self.assertEqual(len(_hits(src)), 1)

    def test_nested_catches_use_their_own_variable(self):
        src = (
            "catch (Exception outer)\n{\n"
            "  try { G(); }\n"
            "  catch (IOException inner)\n  {\n    throw inner;\n  }\n"
            "  throw outer;\n}\n"
        )
        hits = _hits(src)
        self.assertEqual(len(hits), 2)
        self.assertEqual({h.snippet for h in hits}, {"throw inner;", "throw outer;"})

    def test_inner_variable_not_in_scope_of_outer_rethrow(self):
        # throwing the inner variable from the outer block must not match
        src = (
            "catch (Exception outer)\n{\n"
            "  try { G(); } catch (IOException inner) { Log(); }\n"
            "  throw inner;\n}\n"
        )
        self.assertEqual(_hits(src), [])


class EmptyCatchTests(unittest.TestCase):
    def test_empty_catch_with_variable(self):
        hits = _hits_for("try { F(); }\ncatch (Exception ex)\n{\n}\n", _EMPTY_CATCH)
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.line, 2)
        self.assertEqual(h.source_pattern_id, "130:catch-blocks/empty-catch")
        self.assertEqual(h.confidence, "candidate")
        self.assertIn("no intentional marker", h.notes)

    def test_typed_empty_catch_without_variable_matched(self):
        hits = _hits("catch (Exception)\n{\n}\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].locator_id, _EMPTY_CATCH)

    def test_bare_empty_catch_matched(self):
        hits = _hits("catch\n{\n}\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].locator_id, _EMPTY_CATCH)

    def test_filtered_empty_catch_matched(self):
        hits = _hits("catch (Exception ex) when (ex.Message != null)\n{\n}\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].locator_id, _EMPTY_CATCH)

    def test_non_empty_catch_not_matched(self):
        self.assertEqual(_hits_for("catch (Exception ex)\n{\n Log(ex);\n}\n", _EMPTY_CATCH), [])

    def test_comment_only_catch_is_empty_with_marker_note(self):
        hits = _hits("catch (Exception ex)\n{\n // intentionally ignored\n}\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].locator_id, _EMPTY_CATCH)
        self.assertIn("intentional marker", hits[0].notes)

    def test_block_comment_only_catch_flagged_with_marker_note(self):
        hits = _hits_for("catch (Exception ex)\n{\n /* swallow */\n}\n", _EMPTY_CATCH)
        self.assertEqual(len(hits), 1)
        self.assertIn("intentional marker", hits[0].notes)

    def test_empty_statement_catch_not_flagged(self):
        # `{ ; }` carries a token; treated as non-empty
        self.assertEqual(_hits_for("catch (Exception ex)\n{\n ;\n}\n", _EMPTY_CATCH), [])

    def test_only_empty_catch_among_several(self):
        src = (
            "try { F(); }\n"
            "catch (IOException io) { Log(io); }\n"
            "catch (Exception ex) { }\n"
        )
        hits = _hits_for(src, _EMPTY_CATCH)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].line, 3)

    def test_nested_block_in_catch_not_empty(self):
        src = "catch (Exception ex)\n{\n if (a) { }\n}\n"
        self.assertEqual(_hits_for(src, _EMPTY_CATCH), [])

    def test_hits_are_sorted_by_location_then_locator_id(self):
        src = "catch (Exception ex)\n{\n throw ex;\n}\n" "catch (Exception ex)\n{\n}\n"
        hits = _hits(src)
        self.assertEqual(
            [h.locator_id for h in hits],
            [_THROW_VARIABLE_RETHROW, _EMPTY_CATCH],
        )


class ScopeTests(unittest.TestCase):
    def test_generated_files_excluded_and_declared(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Real.cs").write_text("catch (Exception ex)\n{\n throw ex;\n}\n", encoding="utf-8")
            (root / "Gen.g.cs").write_text("catch (Exception ex)\n{\n throw ex;\n}\n", encoding="utf-8")
            hits, scope = scan_paths([root], root=root)
            self.assertEqual([h.file for h in hits], ["Real.cs"])
            self.assertIn("Gen.g.cs", scope.excluded_generated)
            self.assertEqual(scope.enabled_locators, list(_ENABLED_LOCATORS))

    def test_tests_excluded_by_default_and_declared(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tdir = root / "App.Tests"
            tdir.mkdir()
            (tdir / "FooTests.cs").write_text("catch (Exception ex)\n{\n throw ex;\n}\n", encoding="utf-8")
            hits, scope = scan_paths([root], root=root)
            self.assertEqual(hits, [])
            self.assertFalse(scope.tests_included)
            self.assertIn("App.Tests/FooTests.cs", scope.excluded_tests)
            hits2, scope2 = scan_paths([root], include_tests=True, root=root)
            self.assertEqual(len(hits2), 1)
            self.assertTrue(scope2.tests_included)
            self.assertEqual(scope2.excluded_tests, [])

    def test_non_test_file_name_containing_test_substring_not_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "Contest.cs").write_text("catch (Exception ex)\n{\n throw ex;\n}\n", encoding="utf-8")
            hits, scope = scan_paths([root], root=root)
            self.assertEqual(len(hits), 1)
            self.assertIn("Contest.cs", scope.included_files)


if __name__ == "__main__":
    unittest.main()
