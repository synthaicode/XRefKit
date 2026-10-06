from __future__ import annotations

import unittest

from mcp.types import ClientCapabilities, Implementation, InitializeRequestParams

from xrefkit.mcp.server import _initialize_protocol_selection


class _Session:
    def __init__(self, extra: object) -> None:
        self._client_params = type("Params", (), {"model_extra": extra})()


class _Context:
    def __init__(self, extra: object) -> None:
        self.session = _Session(extra)


class InitializeProtocolSelectionTests(unittest.TestCase):
    def test_exclusion_extension_is_retained_in_model_extra(self) -> None:
        params = InitializeRequestParams(
            protocolVersion="2025-03-26",
            capabilities=ClientCapabilities(),
            clientInfo=Implementation(name="test-client", version="1"),
            xrefkit={"excluded_protocols": ["reporting"]},
        )

        selection = _initialize_protocol_selection(_Context(params.model_extra), None)

        self.assertEqual(selection["excluded_protocols"], ["reporting"])
        self.assertEqual(selection["selection_source"], "initialize")

    def test_empty_exclusion_overrides_legacy_server_default(self) -> None:
        selection = _initialize_protocol_selection(
            _Context({"xrefkit": {"excluded_protocols": []}}),
            ["workflow"],
        )

        self.assertEqual(selection["excluded_protocols"], [])
        self.assertNotIn("initial_protocols", selection)

    def test_legacy_include_extension_remains_supported(self) -> None:
        selection = _initialize_protocol_selection(
            _Context({"xrefkit": {"initial_protocols": ["workflow"]}}),
            ["reporting"],
        )

        self.assertEqual(selection["initial_protocols"], ["workflow"])
        self.assertEqual(selection["selection_source"], "initialize")

    def test_server_legacy_default_remains_when_initialize_has_no_selection(self) -> None:
        selection = _initialize_protocol_selection(
            _Context({"xrefkit": {}}),
            ["reporting"],
        )

        self.assertEqual(selection["initial_protocols"], ["reporting"])
        self.assertEqual(selection["selection_source"], "server")

    def test_both_selection_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "both"):
            _initialize_protocol_selection(
                _Context(
                    {
                        "xrefkit": {
                            "excluded_protocols": [],
                            "initial_protocols": [],
                        }
                    }
                ),
                None,
            )

    def test_xrefkit_extension_must_be_an_object(self) -> None:
        with self.assertRaisesRegex(ValueError, "object"):
            _initialize_protocol_selection(_Context({"xrefkit": []}), None)


if __name__ == "__main__":
    unittest.main()
