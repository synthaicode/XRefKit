"""Installed native discovery, exact draft binding and portable references."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest

from xrefkit.discovery import DiscoveredSkillPackage, discover_skill_packages
from xrefkit.loaders import load_package_manifest
from xrefkit.mcp.catalog import XRefCatalog, _build_package_skills
from xrefkit_skills_project_management import package_root


# Core compatibility runs this suite against published and candidate packages.
# Keep explicit release expectations so missing new assets cannot pass silently.
BASE_SKILLS = ('progress_rules_setup', 'requirements_discovery_coordination', 'work_progress_coordination')
RELEASE_SKILLS = {
    '0.1.0a1': BASE_SKILLS,
    '0.1.0a2': BASE_SKILLS + ('pm_coordination_setup', 'pm_decision_coordination'),
}
INSTALLED_VERSION = version('xrefkit-skills-project-management')
EXPECTED_SKILLS = RELEASE_SKILLS[INSTALLED_VERSION]


def package():
    matches=[p for p in discover_skill_packages() if p.package_id=='xrefkit.skills.project_management']
    assert len(matches)==1
    return matches[0]


def test_installed_discovery_and_governance(tmp_path):
    candidate=package()
    catalog=XRefCatalog.build(tmp_path,discover_packages=True)
    entries={e.skill_id:e for e in catalog.skills if e.package_id==candidate.package_id}
    assert str(candidate.manifest.version)==INSTALLED_VERSION
    assert set(entries)==set(EXPECTED_SKILLS)
    for provided in candidate.manifest.provides.skills:
        entry=entries[provided.id]
        assert entry.maturity=='draft'
        assert entry.maturity_governance['promotion']['decision']=='not_requested'
        assert entry.definition_format=='skill_definition_v1'
        body=(package_root()/provided.path).read_bytes()
        governance=json.loads((package_root()/provided.governance_path).read_text())
        assert governance['definition_content_hash']==hashlib.sha256(body).hexdigest()
        assert catalog.get_skill(provided.id)['skill_content'].encode()==body


@pytest.mark.parametrize('sid',EXPECTED_SKILLS)
def test_packaged_draft_cannot_run(sid,tmp_path):
    provided=next(p for p in package().manifest.provides.skills if p.id==sid)
    command=[sys.executable,'-I','-m','xrefkit','skill','run','--root',str(package_root()),
             '--definition',provided.path,'--governance',provided.governance_path,
             '--task','readiness rejection test','--capability','coordination','--tuning','test',
             '--responsibility','refuse draft execution','--execution-mode','subagent_required',
             '--out',str(tmp_path/'must-not-exist.md'),'--json']
    result=subprocess.run(command,cwd=tmp_path,capture_output=True,text=True,encoding='utf-8')
    data=json.loads(result.stdout)
    assert result.returncode!=0 and not data['ok']
    assert any('draft' in e for e in data['errors'])
    assert data['run_log'] is None and not (tmp_path/'must-not-exist.md').exists()


@pytest.mark.parametrize('damage',['hash','identity','missing','escape'])
def test_damaged_governance_refuses_catalog(tmp_path,damage):
    root=tmp_path/'copy'
    shutil.copytree(package_root(),root)
    manifest=load_package_manifest(root/'package_manifest.yaml')
    provided=manifest.provides.skills[0]
    path=root/provided.governance_path
    if damage=='missing': path.unlink()
    elif damage=='escape': provided.governance_path='../outside.json'
    else:
        value=json.loads(path.read_text())
        value['definition_content_hash' if damage=='hash' else 'skill_id']='0'*64 if damage=='hash' else 'wrong_skill'
        path.write_text(json.dumps(value))
    candidate=DiscoveredSkillPackage('copy',root,root/'package_manifest.yaml',manifest)
    with pytest.raises((ValueError,FileNotFoundError)):
        _build_package_skills(candidate)


def test_packaged_links_are_local_or_explicit_navigation():
    for path in package_root().rglob('*.md'):
        for relative in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',path.read_text()):
            if '://' in relative:
                assert relative.startswith('https://github.com/synthaicode/XRefKit/')
                continue
            target=(path.parent/relative).resolve()
            assert target.is_relative_to(package_root().resolve()) and target.is_file()


def test_package_contains_no_project_configuration_or_adapter():
    manifest=load_package_manifest(package_root()/'package_manifest.yaml')
    assert len(manifest.provides.skills)==len(EXPECTED_SKILLS)
    assert not manifest.provides.knowledge
    assert not list(package_root().rglob('*.skill.yaml'))
    source=json.loads((package_root()/'source_manifest.json').read_text())
    assert len(source['sources'])==len(EXPECTED_SKILLS)+3
