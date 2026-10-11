from pathlib import Path

import pytest

from tools.site_release_metadata import render_release


REPO = "synthaicode/XRefKit"
ROOT = Path(__file__).resolve().parents[1]


def release(**changes):
    return {
        "tag_name": "v1.2.3", "draft": False, "prerelease": False,
        "published_at": "2026-11-02T03:04:05Z",
        "html_url": f"https://github.com/{REPO}/releases/tag/v1.2.3",
        **changes,
    }


@pytest.fixture
def site(tmp_path):
    for name in ("index.html", "common/index.html"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / "site/sources" / name).read_bytes())
    return tmp_path


def test_renders_actual_pages_and_is_idempotent(site):
    render_release(site, release(), REPO)
    index = (site / "index.html").read_text(encoding="utf-8")
    assert '/releases/tag/v1.2.3">v1.2.3</a>' in index
    assert '<time datetime="2026-11-02">November 2, 2026</time>' in index
    assert f'https://github.com/{REPO}/tree/v1.2.3' in (site / "common/index.html").read_text(encoding="utf-8")
    before = (site / "index.html").read_bytes()
    render_release(site, release(), REPO)
    assert (site / "index.html").read_bytes() == before


@pytest.mark.parametrize("changes", [
    {"draft": True}, {"prerelease": True}, {"prerelease": None},
    {"tag_name": "v1.2.3-rc1"}, {"tag_name": 'v1.2.3"><script>'},
    {"tag_name": "skills-v1.2.3"}, {"published_at": None},
    {"published_at": "invalid"}, {"published_at": "2026-11-02"},
    {"html_url": "https://example.com/releases/tag/v1.2.3"},
])
def test_invalid_metadata_does_not_change_pages(site, changes):
    before = (site / "index.html").read_bytes()
    with pytest.raises(ValueError):
        render_release(site, release(**changes), REPO)
    assert (site / "index.html").read_bytes() == before


def test_missing_second_marker_does_not_partially_update(site):
    before = (site / "index.html").read_bytes()
    (site / "common/index.html").write_text("no marker", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        render_release(site, release(), REPO)
    assert (site / "index.html").read_bytes() == before


def test_utc_publication_date(site):
    render_release(site, release(published_at="2026-11-02T00:30:00+09:00"), REPO)
    assert 'datetime="2026-11-01"' in (site / "index.html").read_text(encoding="utf-8")
