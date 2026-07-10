from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from xrefkit.mcp.server import (
    SERVER_VERSION,
    _endpoint_info,
    _log_xid_query,
    _should_return_endpoint_info,
    _validate_distribution_configuration,
    _validate_tls_configuration,
)


class StreamableHttpProbeTests(unittest.TestCase):
    def test_executable_distribution_requires_out_of_band_trust_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "distribution-trust-id"):
            _validate_distribution_configuration(
                "streamable-http", "127.0.0.1", None, None, True, None
            )

    def test_remote_distribution_requires_https_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires TLS"):
            _validate_distribution_configuration(
                "streamable-http", "0.0.0.0", "http://example.test", None, True, "release-v1"
            )

    def test_local_distribution_accepts_pinned_trust_id(self) -> None:
        _validate_distribution_configuration(
            "streamable-http", "127.0.0.1", None, None, True, "release-v1"
        )

    def test_plain_get_to_mcp_endpoint_returns_endpoint_info(self) -> None:
        self.assertTrue(
            _should_return_endpoint_info(
                "GET",
                "/mcp",
                {"accept": "text/html,*/*"},
                "/mcp",
            )
        )

    def test_streamable_http_get_stays_with_mcp_transport(self) -> None:
        self.assertFalse(
            _should_return_endpoint_info(
                "GET",
                "/mcp",
                {"accept": "application/json, text/event-stream"},
                "/mcp",
            )
        )

    def test_post_stays_with_mcp_transport(self) -> None:
        self.assertFalse(
            _should_return_endpoint_info(
                "POST",
                "/mcp",
                {"accept": "application/json"},
                "/mcp",
            )
        )

    def test_endpoint_info_is_actionable_for_browser_probe(self) -> None:
        info = _endpoint_info("/mcp")

        self.assertEqual(info["server"], "xrefkit-mcp")
        self.assertEqual(info["version"], SERVER_VERSION)
        self.assertEqual(info["transport"], "streamable-http")
        self.assertEqual(info["endpoint"], "/mcp")
        self.assertIn("Accept: application/json, text/event-stream", info["message"])


class TlsConfigurationTests(unittest.TestCase):
    def test_cert_and_key_enable_tls_for_streamable_http(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certfile = Path(temp_dir, "fullchain.pem")
            keyfile = Path(temp_dir, "privkey.pem")
            certfile.touch()
            keyfile.touch()

            _validate_tls_configuration("streamable-http", certfile, keyfile)

    def test_cert_and_key_must_be_provided_together(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certfile = Path(temp_dir, "fullchain.pem")
            certfile.touch()

            with self.assertRaisesRegex(ValueError, "must be provided together"):
                _validate_tls_configuration("streamable-http", certfile, None)

    def test_tls_is_rejected_for_stdio(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certfile = Path(temp_dir, "fullchain.pem")
            keyfile = Path(temp_dir, "privkey.pem")
            certfile.touch()
            keyfile.touch()

            with self.assertRaisesRegex(ValueError, "only with --transport streamable-http"):
                _validate_tls_configuration("stdio", certfile, keyfile)

    def test_missing_tls_file_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certfile = Path(temp_dir, "missing-fullchain.pem")
            keyfile = Path(temp_dir, "missing-privkey.pem")

            with self.assertRaisesRegex(ValueError, "certificate file does not exist"):
                _validate_tls_configuration("streamable-http", certfile, keyfile)


class ServerXidQueryLogTests(unittest.TestCase):
    def test_logs_xid_queries(self) -> None:
        with self.assertLogs("xrefkit.mcp.server", level="INFO") as captured:
            _log_xid_query("get_document_by_xid", "8A666C1FD121", "abc123")

        self.assertIn("tool=get_document_by_xid", captured.output[0])
        self.assertIn("xid=8A666C1FD121", captured.output[0])
        self.assertIn("known_version=abc123", captured.output[0])


if __name__ == "__main__":
    unittest.main()
