from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from xrefkit.mcp.legacy_resources import (
    manifest_version, materialize_legacy_resources, read_resource_manifest,
    relative_path, resource_file, validate_resource_manifest,
)


def fixture_bundle():
    files = {'tools/common.py': b'VALUE = 42\r\n', 'tools/run.py': b'from common import VALUE\nprint(VALUE)\n',
             'tests/input.bin': bytes([0, 255, 1])}
    rows = [{'path': path, 'content_hash': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}
            for path, data in sorted(files.items())]
    return {'schema_version': 1, 'version': manifest_version(rows), 'files': rows,
            'skills': [{'source': 'skills/a', 'resources': list(files)},
                       {'source': 'skills/b', 'resources': ['tools/common.py']}]}, files


def test_roundtrip_preserves_shared_tree_binary_and_crlf(tmp_path):
    manifest, files = fixture_bundle()
    root = tmp_path / 'server' / 'tools' / 'legacy'
    root.mkdir(parents=True)
    (root / 'legacy-resources.json').write_text(json.dumps(manifest), encoding='utf-8')
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    _, received = read_resource_manifest(tmp_path / 'server', 'legacy')
    def fetch(path):
        response = resource_file(tmp_path / 'server', 'legacy', path)
        return base64.b64decode(response['content'], validate=True)
    cached = materialize_legacy_resources(received, fetch, tmp_path / 'client')
    assert cached != root
    assert (cached / 'tools/common.py').read_bytes() == files['tools/common.py']
    assert (cached / 'tests/input.bin').read_bytes() == files['tests/input.bin']
    def no_fetch(path):
        raise AssertionError('same version must use cache')
    assert materialize_legacy_resources(received, no_fetch, tmp_path / 'client') == cached
    (cached / 'tools/common.py').write_bytes(b'tampered')
    with pytest.raises(ValueError, match='mismatch'):
        materialize_legacy_resources(received, no_fetch, tmp_path / 'client')


@pytest.mark.parametrize('path', ['../secret', '/abs', 'C:/secret', 'tools\\x.py', 'tools/CON.py', 'a//b', 'a./b', 'a\x00b'])
def test_rejects_nonportable_paths(path):
    with pytest.raises(ValueError):
        relative_path(path)


def test_rejects_corrupted_download_without_publishing_cache(tmp_path):
    manifest, files = fixture_bundle()
    with pytest.raises(ValueError, match='mismatch'):
        materialize_legacy_resources(manifest, lambda path: b'changed', tmp_path)
    assert not (tmp_path / manifest['version']).exists()


def test_rejects_undeclared_missing_and_case_alias_resources():
    manifest, files = fixture_bundle()
    with pytest.raises(ValueError, match='file set'):
        validate_resource_manifest(manifest, {**files, 'secret': b'secret'})
    manifest['skills'][0]['resources'].append('missing.py')
    with pytest.raises(ValueError, match='missing resource'):
        validate_resource_manifest(manifest)
    manifest, files = fixture_bundle()
    manifest['files'].append({**manifest['files'][0], 'path': manifest['files'][0]['path'].upper()})
    manifest['version'] = manifest_version(manifest['files'])
    with pytest.raises(ValueError, match='duplicate'):
        validate_resource_manifest(manifest)


def test_rejects_extra_cache_code(tmp_path):
    manifest, files = fixture_bundle()
    cached = materialize_legacy_resources(manifest, files.__getitem__, tmp_path)
    (cached / 'sitecustomize.py').write_text('unexpected', encoding='utf-8')
    with pytest.raises(ValueError, match='file set'):
        materialize_legacy_resources(manifest, files.__getitem__, tmp_path)


def test_manifest_metadata_and_cache_manifest_tamper(tmp_path):
    from xrefkit.mcp.legacy_resources import manifest_hash
    manifest, files = fixture_bundle()
    trusted = manifest_hash(manifest)
    cached = materialize_legacy_resources(manifest, files.__getitem__, tmp_path, expected_manifest_hash=trusted)
    manifest['skills'][0]['source'] = 'skills/changed'
    with pytest.raises(ValueError, match='identity mismatch'):
        materialize_legacy_resources(manifest, files.__getitem__, tmp_path, expected_manifest_hash=trusted)
    with pytest.raises(ValueError, match='manifest mismatch'):
        materialize_legacy_resources(manifest, files.__getitem__, tmp_path)
    manifest['skills'][0]['source'] = 'skills/a'
    (cached / 'legacy-resources.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='manifest mismatch'):
        materialize_legacy_resources(manifest, files.__getitem__, tmp_path)


def test_safe_fixture_run_repeat_reuses_verified_cache(tmp_path):
    import subprocess
    import sys
    manifest, files = fixture_bundle()
    for _ in range(2):
        cached = materialize_legacy_resources(manifest, files.__getitem__, tmp_path)
        result = subprocess.run([sys.executable, '-B', 'tools/run.py'], cwd=cached,
                                capture_output=True, text=True, check=True)
        assert result.stdout.strip() == '42'


def test_live_http_distribution_to_separate_client(tmp_path):
    import socket
    import subprocess
    import sys
    import time
    from xrefkit.mcp.bootstrap import http_post_json, parse_jsonrpc_response
    pytest.importorskip('mcp')
    manifest, files = fixture_bundle()
    server = tmp_path / 'server'
    bundle = server / 'tools' / 'legacy'
    bundle.mkdir(parents=True)
    (bundle / 'legacy-resources.json').write_text(json.dumps(manifest), encoding='utf-8')
    for path, content in files.items():
        target = bundle / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    endpoint = f'http://127.0.0.1:{port}/mcp'
    with (tmp_path / 'server.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, '-m', 'xrefkit', 'mcp', 'serve', '--repo', str(server),
                                 '--transport', 'streamable-http', '--host', '127.0.0.1', '--port', str(port)],
                                stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 20
            while True:
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.1):
                        break
                except OSError:
                    if proc.poll() is not None or time.monotonic() > deadline:
                        pytest.fail('HTTP server did not start: ' + (tmp_path / 'server.log').read_text(encoding='utf-8'))
                    time.sleep(.05)
            raw, headers = http_post_json(endpoint, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                'params': {'protocolVersion': '2025-03-26', 'capabilities': {},
                           'clientInfo': {'name': 'resource-test', 'version': '1'}}}, None)
            assert 'result' in parse_jsonrpc_response(raw)
            session_headers = {'mcp-session-id': headers['mcp-session-id']}
            http_post_json(endpoint, {'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}}, None, session_headers)
            request_id = 1
            def call(name, arguments):
                nonlocal request_id
                request_id += 1
                raw, _ = http_post_json(endpoint, {'jsonrpc': '2.0', 'id': request_id, 'method': 'tools/call',
                    'params': {'name': name, 'arguments': arguments}}, None, session_headers)
                result = parse_jsonrpc_response(raw)['result']
                assert not result.get('isError'), result
                return result.get('structuredContent') or json.loads(result['content'][0]['text'])
            call('get_startup_context', {})
            received = call('get_legacy_resource_manifest', {'namespace': 'legacy'})
            def fetch(path):
                response = call('get_legacy_resource_file', {'namespace': 'legacy', 'path': path})
                assert response['version'] == received['version']
                return base64.b64decode(response['content'], validate=True)
            cached = materialize_legacy_resources(received, fetch, tmp_path / 'client')
            result = subprocess.run([sys.executable, '-B', 'tools/run.py'], cwd=cached,
                                    capture_output=True, text=True, check=True)
            assert result.stdout.strip() == '42'
        finally:
            proc.terminate()
            proc.wait(timeout=10)


def test_empty_core_bootstrap_skill_and_client_run(tmp_path):
    import subprocess
    import sys
    from xrefkit.mcp.catalog import XRefCatalog
    server = tmp_path / 'empty-server'
    client = tmp_path / 'empty-client'
    server.mkdir()
    client.mkdir()
    catalog = XRefCatalog.build(server, discover_packages=False)
    skill = catalog.get_skill('legacy_flow_skill_migration')
    assert skill['maturity'] == 'unassessed'
    assert skill['repository_adoption']['adopted']
    assert skill['repository_adoption']['legacy_maturity'] == 'trial'
    assert catalog.get_document_by_xid('7B3E5D1A6104')['content']
    assert catalog.get_document_by_xid('9DD40488BB9D')['content']
    assert catalog.get_client_tool_file('tools/migrate_legacy_flow_skill.py')['content']
    definition = client / 'migration.SKILL.v1.md'
    definition.write_bytes(skill['skill_content'].encode('utf-8'))
    result = subprocess.run([sys.executable, '-m', 'xrefkit', 'skill', 'run', '--root', str(client),
        '--definition', str(definition), '--task', 'Inspect the old environment and prepare migration tasks',
        '--capability', 'legacy migration', '--tuning', 'Python resource migration',
        '--responsibility', 'inventory and prepare migration with explicit gaps',
        '--execution-mode', 'local_default', '--json'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    snapshot = catalog.contribution_source_snapshot(skill_id=skill['skill_id'], package_id=skill['package_id'],
        skill_content_hash=hashlib.sha256(definition.read_bytes()).hexdigest(), knowledge_versions=[], provider_version='test')
    assert snapshot['verification'] == 'matched_current_catalog'
    with pytest.raises(ValueError, match='does not match'):
        catalog.contribution_source_snapshot(skill_id=skill['skill_id'], package_id=skill['package_id'],
            skill_content_hash='0' * 64, knowledge_versions=[], provider_version='test')
