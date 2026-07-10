from __future__ import annotations

import unittest
import json
import multiprocessing
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
from xrefkit.mcp.audit import McpAuditLog, SessionRunBinding, SessionRunRegistry, _write_all


def _append_audit_events(path: str, run_id: str) -> None:
    audit = McpAuditLog(Path(path))
    binding = SessionRunBinding(
        run_id=run_id,
        mcp_session_id="mcp-1",
        repository_fingerprint="repo-1",
        skill_id="sample_skill",
    )
    for index in range(20):
        audit.append("xid.resolved", binding=binding, xid=f"XID-{index}")


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
    def test_write_all_retries_short_writes(self) -> None:
        writes: list[bytes] = []

        def short_write(_fd: int, data: bytes) -> int:
            writes.append(data)
            return min(2, len(data))

        _write_all(0, b"abcdef", write=short_write)

        self.assertEqual([b"abcdef", b"cdef", b"ef"], writes)

    def test_audit_log_is_parseable_after_concurrent_process_appends(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = str(Path(temp_dir) / "xid_audit.jsonl")
            run_ids = ["d4c0ca07-ec6c-48f9-b296-ec735323b088", "cb796f8c-9d89-4a6f-906a-34ff5a891873"]
            context = multiprocessing.get_context("spawn")
            processes = [context.Process(target=_append_audit_events, args=(path, run_id)) for run_id in run_ids]
            for process in processes:
                process.start()
            for process in processes:
                process.join(30)
                self.assertEqual(0, process.exitcode)

            events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
            self.assertEqual(40, len(events))
    def test_skill_run_binding_is_idempotent_and_requires_explicit_end(self) -> None:
        class Session:
            pass

        registry = SessionRunRegistry()
        session = Session()
        binding = registry.bind(
            session,
            run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
            repository_fingerprint="repo-1",
            skill_id="sample_skill",
        )
        self.assertIs(binding, registry.bind(
            session,
            run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
            repository_fingerprint="repo-1",
            skill_id="sample_skill",
        ))
        with self.assertRaisesRegex(ValueError, "already bound"):
            registry.bind(
                session,
                run_id="cb796f8c-9d89-4a6f-906a-34ff5a891873",
                repository_fingerprint="repo-1",
                skill_id="sample_skill",
            )
        self.assertEqual(binding, registry.end(session, run_id=binding.run_id))
        self.assertIsNone(registry.current(session))
    def test_logs_xid_queries(self) -> None:
        with self.assertLogs("xrefkit.mcp.server", level="INFO") as captured:
            _log_xid_query("get_document_by_xid", "8A666C1FD121", "abc123")

        self.assertIn("tool=get_document_by_xid", captured.output[0])
        self.assertIn("xid=8A666C1FD121", captured.output[0])
        self.assertIn("known_version=abc123", captured.output[0])

    def test_structured_audit_log_correlates_xid_with_bound_run(self) -> None:
        class Session:
            pass

        with TemporaryDirectory() as temp_dir:
            registry = SessionRunRegistry()
            audit = McpAuditLog(Path(temp_dir) / "xid_audit.jsonl")
            session = Session()
            binding = registry.bind(
                session,
                run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
                repository_fingerprint="repo-1",
                skill_id="sample_skill",
            )

            _log_xid_query(
                "get_document_by_xid",
                "8A666C1FD121",
                audit_log=audit,
                binding=binding,
                content_hash="hash-1",
            )

            entry = json.loads(audit.path.read_text(encoding="utf-8"))
            self.assertEqual("xid.resolved", entry["event_type"])
            self.assertEqual(binding.run_id, entry["run_id"])
            self.assertEqual(binding.mcp_session_id, entry["mcp_session_id"])
            self.assertEqual("8A666C1FD121", entry["xid"])
            self.assertEqual("hash-1", entry["content_hash"])

    def test_audit_binding_fields_cannot_be_overridden(self) -> None:
        with TemporaryDirectory() as temp_dir:
            audit = McpAuditLog(Path(temp_dir) / "xid_audit.jsonl")
            binding = SessionRunBinding(
                run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
                mcp_session_id="mcp-1",
                repository_fingerprint="repo-1",
                skill_id="sample_skill",
            )
            event = audit.append(
                "xid.resolved",
                binding=binding,
                run_id="forged-run",
                skill_id="forged-skill",
            )

            self.assertEqual(binding.run_id, event["run_id"])
            self.assertEqual(binding.skill_id, event["skill_id"])
            self.assertEqual("xid.resolved", event["event_type"])


if __name__ == "__main__":
    unittest.main()
