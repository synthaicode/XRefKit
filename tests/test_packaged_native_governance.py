import json
import hashlib
from pathlib import Path

import pytest
import yaml

from xrefkit.discovery import DiscoveredSkillPackage
from xrefkit.loaders import load_package_manifest
from xrefkit.mcp.catalog import _build_package_skills
from xrefkit.models.package_manifest import ProvidedSkill


def fixture(tmp_path):
    root=Path(__file__).resolve().parents[1]
    source=root/'skills/packs/project-management/progress_rules_setup/SKILL.v1.md'
    (tmp_path/'skill.md').write_bytes(source.read_bytes())
    gov=json.loads((root/'governance/skills/progress_rules_setup.json').read_text())
    gov['definition_content_hash']=hashlib.sha256(source.read_bytes()).hexdigest()
    (tmp_path/'governance.json').write_text(json.dumps(gov))
    manifest={'package_id':'test.native','package_type':'skill_package','version':'0.1.0',
              'requires':{'xrefkit_core':'>=2.0.0 <3.0.0'},'contract':{},
              'provides':{'skills':[{'id':'progress_rules_setup','xid':'91F7D3B6A204','path':'skill.md','governance_path':'governance.json'}]}}
    (tmp_path/'package_manifest.yaml').write_text(yaml.safe_dump(manifest))
    return DiscoveredSkillPackage('test',tmp_path,tmp_path/'package_manifest.yaml',load_package_manifest(tmp_path/'package_manifest.yaml'))


def test_bound_native_draft_and_live_hash_check(tmp_path):
    package=fixture(tmp_path)
    assert _build_package_skills(package)[0].maturity=='draft'
    (tmp_path/'skill.md').write_bytes((tmp_path/'skill.md').read_bytes()+b'\nchanged\n')
    with pytest.raises(ValueError,match='content_hash'):
        _build_package_skills(package)


def test_omitted_governance_preserves_existing_unassessed_behavior(tmp_path):
    package=fixture(tmp_path)
    package.manifest.provides.skills[0].governance_path=None
    assert _build_package_skills(package)[0].maturity=='unassessed'


def test_legacy_governance_field_is_rejected():
    with pytest.raises(ValueError,match='native Markdown'):
        ProvidedSkill(id='legacy',xid='legacy.xid',path='legacy.yaml',governance_path='gov.json')

def test_packaged_draft_ranking_is_not_runnable(tmp_path):
    from xrefkit.mcp.catalog import XRefCatalog
    package=fixture(tmp_path)
    catalog=XRefCatalog(tmp_path,'test','test',[],discovered_packages=(package,))
    ranked=catalog.rank_skills_for_purpose('confirm progress rules and destinations')
    row=next(r for r in ranked if r['skill_id']=='progress_rules_setup')
    assert row['maturity']=='draft'
    assert row['execution_readiness']['runnable'] is False
    assert 'draft' in row['execution_readiness']['governance_block_reason']
