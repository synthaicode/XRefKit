from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path

import pytest

from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.contribution_adoption import (
    HmacHumanApprovalVerifier,
    LocalCanonicalAdoptionTransport,
    issue_hmac_approval_assertion,
)
from xrefkit.mcp.contribution_returns import (
    adopt_contribution_return,
    review_contribution_return,
    submit_contribution_return,
)
from xrefkit.mcp.ownership import load_ownership
from xrefkit.mcp.skill_maturity import (
    apply_skill_maturity_proposal,
    assess_skill_maturity,
    propose_skill_maturity,
    review_skill_maturity_proposal,
)

APPROVAL_TEST_KEY = "test-human-approval-" + "key-32-bytes-minimum"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "ownership.yaml",
        """zones:
  - id: kernel-content
    owner: base
    paths:
      - skills/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: false
  - id: records
    owner: operational
    paths:
      - observations/
    catalog: false
    distribution: false
    base_sync: false
    shadowing: false
""",
    )
    _write(tmp_path / "observations" / "seed.md", "# Seed observation\n")
    _write(
        tmp_path / "skills" / "sample" / "meta.md",
        """# Skill Meta: sample

- skill_id: `sample`
- summary: sample review Skill
- use_when: sample work is requested
- input: request
- output: result
- maturity: `trial`
- execution_mode: `subagent_preferred`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `software_development`
- tuning: `sample`
- responsibility: `review`
- os_contract: v1
- constraints: keep the sample boundary explicit
- skill_doc: `./SKILL.md`
- observation_refs:
  - `../../observations/seed.md`
""",
    )
    _write(tmp_path / "skills" / "sample" / "SKILL.md", "# Skill: sample\n\nDo sample work.\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.test")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "seed")
    return tmp_path


def verifier() -> HmacHumanApprovalVerifier:
    return HmacHumanApprovalVerifier(APPROVAL_TEST_KEY)


def file(path: str, content: str) -> dict[str, str]:
    return {
        "path": path,
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def submit_observation(
    root: Path,
    *,
    run_id: str | None = None,
    evidence_id: str = "evidence-1",
    proposed_maturity: str = "stable",
    maturity_at_use: str = "trial",
) -> str:
    run_id = run_id or str(uuid.uuid4())
    contribution_id = str(uuid.uuid4())
    skill_content = (root / "skills" / "sample" / "SKILL.md").read_text(encoding="utf-8")
    skill_hash = hashlib.sha256(skill_content.encode("utf-8")).hexdigest()
    binding = SessionRunBinding(
        run_id=run_id, mcp_session_id=str(uuid.uuid4()),
        repository_fingerprint="a" * 32, skill_id="sample",
    )
    content = f"# Skill observation\n\n- run_id: `{run_id}`\n"
    submit_contribution_return(
        root,
        binding=binding,
        source_snapshot={
            "provider_id": "xrefkit-mcp", "provider_version": "test",
            "package_id": None, "package_version": None, "skill_id": "sample",
            "skill_maturity": maturity_at_use, "skill_content_hash": skill_hash,
            "knowledge_versions": [],
            "verification": "matched_current_catalog",
        },
        contribution_id=contribution_id,
        kind="skill_observation",
        title="Observed sample Skill",
        summary="Return bounded use evidence",
        files=[file("observation.md", content)],
        proposed_target_path=f"observations/{contribution_id}.md",
        skill_observation={
            "skill_id": "sample", "skill_content_hash": skill_hash,
            "maturity_at_use": maturity_at_use, "run_id": run_id,
            "client_id": "vscode-client-1", "execution_environment": "windows-vscode",
            "model_id": "test-model", "outcome": "success", "retry_count": 1,
            "evaluation_evidence": [{
                "evidence_id": evidence_id, "kind": "run-log",
                "reference": "client-run-log", "content_hash": "c" * 64,
            }],
            "ambiguities": ["one boundary needed clarification"],
            "human_evaluation": {
                "evaluation_id": "human-eval-1", "evaluator": "human-reviewer",
                "result": "accepted", "evidence": "Reviewed the run outcome.",
            },
            "proposed_maturity": proposed_maturity,
        },
    )
    return contribution_id


def adopt_observation(root: Path, contribution_id: str) -> None:
    manifest = json.loads(
        (root / ".xrefkit" / "contribution-returns" / contribution_id / "manifest.json").read_text(encoding="utf-8")
    )
    target = manifest["proposed_target_path"]
    path_hash = lambda value: hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    decision_id = str(uuid.uuid4())
    reviewer = "human:observation-reviewer"
    assertion = issue_hmac_approval_assertion(
        APPROVAL_TEST_KEY,
        {
            "assertion_id": str(uuid.uuid4()), "contribution_id": contribution_id,
            "decision_id": decision_id, "decision": "accepted", "reviewer": reviewer,
            "payload_hash": manifest["payload_hash"], "proposed_target_path": target,
            "proposed_target_path_hash": path_hash(target), "approved_target_path": target,
            "approved_target_path_hash": path_hash(target),
        },
    )
    review = review_contribution_return(
        root, contribution_id=contribution_id, decision_id=decision_id,
        decision="accepted", reviewer=reviewer, decision_evidence="Accept observation evidence.",
        approval_assertion=assertion, approved_target_path=target,
        approval_verifier=verifier(), ownership=load_ownership(root),
    )
    adopt_contribution_return(
        root, contribution_id=contribution_id, adoption_id=str(uuid.uuid4()),
        reviewer=reviewer, decision_evidence="Place the reviewed observation.",
        approval_token=review["approval_token"], approval_verifier=verifier(),
        transport=LocalCanonicalAdoptionTransport(), ownership=load_ownership(root),
    )


def reviewed_stable_proposal(root: Path, contribution_id: str) -> tuple[dict, dict]:
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    proposal = propose_skill_maturity(
        root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
        target_maturity="stable", governance_refs=[], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    decision_id = str(uuid.uuid4())
    reviewer = "human:maturity-owner"
    evidence = "Evidence is sufficient."
    assertion = issue_hmac_approval_assertion(
        APPROVAL_TEST_KEY,
        {
            "assertion_id": str(uuid.uuid4()), "proposal_id": proposal["proposal_id"],
            "decision_id": decision_id, "decision": "accepted", "reviewer": reviewer,
            "decision_evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
            "proposal_hash": proposal["event_hash"], "skill_id": "sample",
            "target_maturity": "stable",
            "candidate_meta_content_hash": proposal["candidate_meta_content_hash"],
        },
    )
    review = review_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], decision_id=decision_id,
        decision="accepted", reviewer=reviewer, decision_evidence=evidence,
        approval_assertion=assertion, approval_verifier=verifier(),
    )
    return proposal, review


def test_skill_observation_rejects_prompt_or_secret_fields(tmp_path: Path) -> None:
    root = repo(tmp_path)
    run_id = str(uuid.uuid4())
    skill_hash = hashlib.sha256((root / "skills/sample/SKILL.md").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unsupported or sensitive"):
        submit_contribution_return(
            root,
            binding=SessionRunBinding(run_id, str(uuid.uuid4()), "a" * 32, "sample"),
            source_snapshot={"skill_id": "sample", "skill_content_hash": skill_hash},
            contribution_id=str(uuid.uuid4()), kind="skill_observation", title="x",
            summary="x", files=[file("x.md", "# x\n")],
            skill_observation={"prompt": "do not store this"},
        )


def test_assessment_requires_adopted_observation_to_be_committed(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    with pytest.raises(ValueError, match="committed to Git"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="sample",
            observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_human_reviewed_one_step_maturity_apply_updates_canonical_meta(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    assert assessment["aggregation"]["retry_total"] == 1
    proposal = propose_skill_maturity(
        root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
        target_maturity="stable", governance_refs=[], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    assert proposal["readiness"] == "passed"
    assert proposal["authority"] == "none"
    decision_id = str(uuid.uuid4())
    reviewer = "human:maturity-owner"
    assertion = issue_hmac_approval_assertion(
        APPROVAL_TEST_KEY,
        {
            "assertion_id": str(uuid.uuid4()), "proposal_id": proposal["proposal_id"],
            "decision_id": decision_id, "decision": "accepted", "reviewer": reviewer,
            "decision_evidence_hash": hashlib.sha256(b"Evidence is sufficient.").hexdigest(),
            "proposal_hash": proposal["event_hash"], "skill_id": "sample",
            "target_maturity": "stable",
            "candidate_meta_content_hash": proposal["candidate_meta_content_hash"],
        },
    )
    review = review_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], decision_id=decision_id,
        decision="accepted", reviewer=reviewer, decision_evidence="Evidence is sufficient.",
        approval_assertion=assertion, approval_verifier=verifier(),
    )
    applied = apply_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], apply_id=str(uuid.uuid4()),
        reviewer=reviewer, decision_evidence="Apply reviewed one-step promotion.",
        approval_token=review["approval_token"], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    meta = (root / "skills/sample/meta.md").read_text(encoding="utf-8")
    assert applied["maturity"] == "stable"
    assert "- maturity: `stable`" in meta
    assert f"../../observations/{contribution_id}.md" in meta
    assert applied["publication"] == "not_performed"


def test_skipped_or_downgrade_transition_and_duplicate_evidence_fail_closed(tmp_path: Path) -> None:
    root = repo(tmp_path)
    first = submit_observation(root, evidence_id="shared-evidence")
    second = submit_observation(root, evidence_id="shared-evidence")
    for item in (first, second):
        adopt_observation(root, item)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observations")
    with pytest.raises(ValueError, match="duplicate Skill observation evidence_id"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="sample",
            observation_contribution_ids=[first, second], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[first], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    with pytest.raises(ValueError, match="one-step promotion"):
        propose_skill_maturity(
            root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
            target_maturity="governed", governance_refs=[], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_assessment_rejects_signed_adoption_event_from_another_record(tmp_path: Path) -> None:
    root = repo(tmp_path)
    first = submit_observation(root, evidence_id="evidence-first")
    second = submit_observation(root, evidence_id="evidence-second")
    for item in (first, second):
        adopt_observation(root, item)
    first_event = root / ".xrefkit" / "contribution-returns" / first / "events" / "adoption.json"
    second_event = root / ".xrefkit" / "contribution-returns" / second / "events" / "adoption.json"
    first_event.write_bytes(second_event.read_bytes())
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observations")
    with pytest.raises(ValueError, match="not bound to its manifest"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="sample",
            observation_contribution_ids=[first], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_client_proposed_maturity_has_no_transition_authority(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root, proposed_maturity="governed")
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    proposal = propose_skill_maturity(
        root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
        target_maturity="stable", governance_refs=[], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    assert proposal["target_maturity"] == "stable"
    assert proposal["client_proposed_maturities"] == ["governed"]
    assert proposal["authority"] == "none"


def test_apply_rejects_stale_skill_body_and_wrong_human_token(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    proposal, review = reviewed_stable_proposal(root, contribution_id)
    with pytest.raises(ValueError, match="approval_token"):
        apply_skill_maturity_proposal(
            root, proposal_id=proposal["proposal_id"], apply_id=str(uuid.uuid4()),
            reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
            approval_token="wrong-token", approval_verifier=verifier(),
            ownership=load_ownership(root),
        )
    _write(root / "skills/sample/SKILL.md", "# Skill: sample\n\nChanged after review.\n")
    with pytest.raises(ValueError, match="Skill body changed"):
        apply_skill_maturity_proposal(
            root, proposal_id=proposal["proposal_id"], apply_id=str(uuid.uuid4()),
            reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
            approval_token=review["approval_token"], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_apply_recovery_revalidates_committed_observation(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    proposal, review = reviewed_stable_proposal(root, contribution_id)
    apply_id = str(uuid.uuid4())
    apply_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], apply_id=apply_id,
        reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
        approval_token=review["approval_token"], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    apply_path = root / ".xrefkit/skill-maturity/proposals" / proposal["proposal_id"] / "apply.json"
    apply_path.unlink()
    observation_path = root / "observations" / f"{contribution_id}.md"
    observation_path.write_text("# tampered after prepare\n", encoding="utf-8")
    with pytest.raises(ValueError, match="committed to Git and unchanged"):
        apply_skill_maturity_proposal(
            root, proposal_id=proposal["proposal_id"], apply_id=apply_id,
            reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
            approval_token=review["approval_token"], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_apply_replay_rejects_canonical_meta_changed_after_apply(tmp_path: Path) -> None:
    root = repo(tmp_path)
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    proposal, review = reviewed_stable_proposal(root, contribution_id)
    apply_id = str(uuid.uuid4())
    apply_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], apply_id=apply_id,
        reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
        approval_token=review["approval_token"], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    meta_path = root / "skills/sample/meta.md"
    meta_path.write_text(
        meta_path.read_text(encoding="utf-8") + "\n- tags: `changed-after-apply`\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="changed after the recorded maturity apply"):
        apply_skill_maturity_proposal(
            root, proposal_id=proposal["proposal_id"], apply_id=apply_id,
            reviewer="human:maturity-owner", decision_evidence="Apply reviewed promotion.",
            approval_token=review["approval_token"], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_assessment_excludes_local_pack_skill(tmp_path: Path) -> None:
    root = repo(tmp_path)
    local_meta = root / "packs/local/demo/skills/local-only/meta.md"
    _write(
        local_meta,
        "# Skill Meta: local-only\n\n- skill_id: `local-only`\n- maturity: `trial`\n- skill_doc: `./SKILL.md`\n",
    )
    _write(local_meta.parent / "SKILL.md", "# Skill: local-only\n")
    with pytest.raises(ValueError, match="exactly one repository-owned canonical Skill"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="local-only",
            observation_contribution_ids=[str(uuid.uuid4())],
            approval_verifier=verifier(), ownership=load_ownership(root),
        )


def test_assessment_rejects_duplicate_canonical_skill_identity(tmp_path: Path) -> None:
    root = repo(tmp_path)
    duplicate = root / "skills/duplicate/meta.md"
    _write(
        duplicate,
        (root / "skills/sample/meta.md").read_text(encoding="utf-8"),
    )
    _write(duplicate.parent / "SKILL.md", "# Skill: duplicate sample\n")
    with pytest.raises(ValueError, match="exactly one repository-owned canonical Skill"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="sample",
            observation_contribution_ids=[str(uuid.uuid4())],
            approval_verifier=verifier(), ownership=load_ownership(root),
        )


def test_applied_run_identity_cannot_be_reused_for_later_promotion(tmp_path: Path) -> None:
    root = repo(tmp_path)
    run_id = str(uuid.uuid4())
    first = submit_observation(root, run_id=run_id, evidence_id="first-evidence")
    adopt_observation(root, first)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt first observation")
    proposal, review = reviewed_stable_proposal(root, first)
    apply_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], apply_id=str(uuid.uuid4()),
        reviewer="human:maturity-owner", decision_evidence="Apply stable promotion.",
        approval_token=review["approval_token"], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    second = submit_observation(
        root, run_id=run_id, evidence_id="second-evidence",
        proposed_maturity="governed", maturity_at_use="stable",
    )
    adopt_observation(root, second)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt second observation")
    with pytest.raises(ValueError, match="run_ids already used"):
        assess_skill_maturity(
            root, assessment_id=str(uuid.uuid4()), skill_id="sample",
            observation_contribution_ids=[second], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_proposal_rejects_duplicate_maturity_and_status_fields(tmp_path: Path) -> None:
    root = repo(tmp_path)
    meta_path = root / "skills/sample/meta.md"
    meta_path.write_text(
        meta_path.read_text(encoding="utf-8").replace(
            "- maturity: `trial`", "- status: `trial`\n- maturity: `trial`"
        ),
        encoding="utf-8",
    )
    _git(root, "add", "skills/sample/meta.md")
    _git(root, "commit", "-qm", "add duplicate maturity field")
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    with pytest.raises(ValueError, match="duplicate maturity/status fields"):
        propose_skill_maturity(
            root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
            target_maturity="stable", governance_refs=[], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_governance_ref_change_after_review_blocks_governed_apply(tmp_path: Path) -> None:
    root = repo(tmp_path)
    meta_path = root / "skills/sample/meta.md"
    meta_path.write_text(
        meta_path.read_text(encoding="utf-8").replace(
            "- maturity: `trial`", "- maturity: `stable`"
        ),
        encoding="utf-8",
    )
    _write(root / "docs/governance.md", "# Governance evidence\n")
    _git(root, "add", "skills/sample/meta.md", "docs/governance.md")
    _git(root, "commit", "-qm", "prepare governed candidate")
    contribution_id = submit_observation(
        root, proposed_maturity="governed", maturity_at_use="stable"
    )
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    proposal = propose_skill_maturity(
        root, proposal_id=str(uuid.uuid4()), assessment_id=assessment["assessment_id"],
        target_maturity="governed", governance_refs=["../../docs/governance.md"],
        approval_verifier=verifier(), ownership=load_ownership(root),
    )
    decision_id = str(uuid.uuid4())
    reviewer = "human:maturity-owner"
    evidence = "Governance evidence is sufficient."
    assertion = issue_hmac_approval_assertion(
        APPROVAL_TEST_KEY,
        {
            "assertion_id": str(uuid.uuid4()), "proposal_id": proposal["proposal_id"],
            "decision_id": decision_id, "decision": "accepted", "reviewer": reviewer,
            "decision_evidence_hash": hashlib.sha256(evidence.encode()).hexdigest(),
            "proposal_hash": proposal["event_hash"], "skill_id": "sample",
            "target_maturity": "governed",
            "candidate_meta_content_hash": proposal["candidate_meta_content_hash"],
        },
    )
    review = review_skill_maturity_proposal(
        root, proposal_id=proposal["proposal_id"], decision_id=decision_id,
        decision="accepted", reviewer=reviewer, decision_evidence=evidence,
        approval_assertion=assertion, approval_verifier=verifier(),
    )
    _write(root / "docs/governance.md", "# Replaced governance evidence\n")
    _git(root, "add", "docs/governance.md")
    _git(root, "commit", "-qm", "replace governance evidence")
    with pytest.raises(ValueError, match="governance_refs changed"):
        apply_skill_maturity_proposal(
            root, proposal_id=proposal["proposal_id"], apply_id=str(uuid.uuid4()),
            reviewer=reviewer, decision_evidence="Apply governed promotion.",
            approval_token=review["approval_token"], approval_verifier=verifier(),
            ownership=load_ownership(root),
        )


def test_clean_crlf_observation_is_not_treated_as_stale(tmp_path: Path) -> None:
    root = repo(tmp_path)
    _git(root, "config", "core.autocrlf", "true")
    contribution_id = submit_observation(root)
    adopt_observation(root, contribution_id)
    _git(root, "add", "observations")
    _git(root, "commit", "-qm", "adopt observation")
    observation_path = root / "observations" / f"{contribution_id}.md"
    observation_path.write_bytes(
        observation_path.read_text(encoding="utf-8").replace("\n", "\r\n").encode()
    )
    assert subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", str(observation_path)],
        check=False,
    ).returncode == 0
    assessment = assess_skill_maturity(
        root, assessment_id=str(uuid.uuid4()), skill_id="sample",
        observation_contribution_ids=[contribution_id], approval_verifier=verifier(),
        ownership=load_ownership(root),
    )
    assert assessment["eligibility"] == "eligible_for_proposal"
