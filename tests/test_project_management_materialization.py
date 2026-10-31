import json
import shutil
from pathlib import Path

import pytest

from tools.materialize_project_management_package import generate, main, PACKAGE


def test_approved_bytes_cannot_be_rebound_after_link_transform(tmp_path):
    root=Path(__file__).resolve().parents[1]
    for rel in ['skills','governance','docs']:
        # Source links resolve against the actual tree; copy only governed inputs,
        # then use the real remaining targets through a full temporary fixture.
        shutil.copytree(root/rel,tmp_path/rel)
    gp=tmp_path/'governance/skills/requirements_discovery_coordination.json'
    record=json.loads(gp.read_text())
    record['maturity']='trial'
    record['promotion']['decision']='approved'
    gp.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='separate package governance'):
        generate(tmp_path)


def test_stale_extra_managed_asset_is_rejected(tmp_path,monkeypatch):
    target=tmp_path/PACKAGE/'skills'
    target.mkdir(parents=True)
    (target/'retired.md').write_text('stale')
    monkeypatch.setattr('tools.materialize_project_management_package.generate',lambda root:{})
    monkeypatch.setattr('sys.argv',['materialize','--root',str(tmp_path),'--check'])
    with pytest.raises(SystemExit,match='unexpected managed asset'):
        main()


def test_embedded_migration_adoption_matches_raw_bytes():
    from xrefkit.repository_skills import load_repository_adoption
    import xrefkit
    root=Path(xrefkit.__file__).parent/'resources/migration'
    assert load_repository_adoption(root)['entries']
