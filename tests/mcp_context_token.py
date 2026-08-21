import unittest

from xrefkit.mcp.context_token import ContextTokenCodec


class ContextTokenTests(unittest.TestCase):
    def test_round_trip_and_refresh_preserve_context(self) -> None:
        codec = ContextTokenCodec("test-secret", "repo-1", ttl_seconds=60)
        token = codec.issue(startup_loaded=True)
        claims = codec.verify(token)
        self.assertTrue(claims.startup_loaded)

        refreshed = codec.refresh(
            claims,
            client_tools_unlocked=True,
            run_id="run-1",
            skill_id="sample_skill",
            mcp_session_id=claims.context_id,
        )
        updated = codec.verify(refreshed)
        self.assertEqual(claims.context_id, updated.context_id)
        self.assertTrue(updated.client_tools_unlocked)
        self.assertEqual("sample_skill", updated.skill_id)

    def test_round_trip_preserves_prompt_flow_correlation(self) -> None:
        codec = ContextTokenCodec("test-secret", "repo-1", ttl_seconds=60)
        token = codec.issue(
            startup_loaded=True,
            flow_id="FLOW-001",
            root_run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
            parent_run_id="d4c0ca07-ec6c-48f9-b296-ec735323b088",
            work_item_id="WI-001",
            node_id="node-001",
        )
        claims = codec.verify(token)

        self.assertEqual("FLOW-001", claims.flow_id)
        self.assertEqual("WI-001", claims.work_item_id)

    def test_tampering_and_repository_mismatch_are_rejected(self) -> None:
        codec = ContextTokenCodec("test-secret", "repo-1", ttl_seconds=60)
        token = codec.issue(startup_loaded=True)
        body, signature = token.rsplit(".", 1)
        tampered = f"{body[:-1]}x.{signature}"
        with self.assertRaises(ValueError):
            codec.verify(tampered)
        with self.assertRaises(ValueError):
            ContextTokenCodec("test-secret", "repo-2").verify(token)


if __name__ == "__main__":
    unittest.main()
