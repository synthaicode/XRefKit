"""Exercise the acquisition CLI with real pip and a local, pinned fixture wheelhouse."""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread
from time import monotonic, sleep
import unittest
import zipfile
from uuid import uuid4

from xrefkit_openai_runtime.acquisition import _target


_COMMAND = """
import sys
sys.path.insert(0, sys.argv.pop(1))
from xrefkit_openai_runtime import acquisition
mode = sys.argv.pop(1)
if mode == 'interrupt':
    import os
    run = acquisition._run
    def stop_before_install(*args, step, **kwargs):
        if step == 'install verified wheel set':
            os._exit(73)
        return run(*args, step=step, **kwargs)
    acquisition._run = stop_before_install
if mode == 'desktop-stop':
    run = acquisition._run
    def pause_install(python, args, *, step, **kwargs):
        if step == 'install verified wheel set':
            command = (
                'import subprocess, sys, time; from pathlib import Path; '
                'p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"]); '
                'Path("installer.pid").write_text(str(p.pid))'
            )
            return run(python, ["-c", command], step=step, **kwargs)
        return run(python, args, step=step, **kwargs)
    acquisition._run = pause_install
if sys.argv[1] == "desktop":
    sys.argv.pop(1)
    sys.path.insert(0, sys.argv.pop(1))
    from xrefkit_openai_runtime.host import main
    raise SystemExit(main())
raise SystemExit(acquisition.main())
"""
_SOURCE = Path(__file__).resolve().parents[1] / "src"


def _wheel(directory, name, files, dependencies=""):
    identity = f"{name}-1.0"
    metadata = f"{identity}.dist-info"
    path = directory / f"{identity}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        for entry, data in files.items():
            archive.writestr(entry, data)
        archive.writestr(f"{metadata}/METADATA",
                         f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n{dependencies}")
        archive.writestr(f"{metadata}/WHEEL",
                         "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        archive.writestr(f"{metadata}/RECORD", "".join(f"{path},,\n" for path in files))
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _process_has_ended(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            return ctypes.get_last_error() == 87  # ERROR_INVALID_PARAMETER (PID does not exist)
        try:
            return kernel.WaitForSingleObject(handle, 2000) == 0
        finally:
            kernel.CloseHandle(handle)
    status = Path(f"/proc/{pid}/stat")
    try:
        return status.read_text().rsplit(") ", 1)[1][0] == "Z"
    except FileNotFoundError:
        return True


class TestRuntimeAcquisition(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xr-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.cache, self.wheelhouse, self.lock = root / "cache", root / "wheels", root / "lock.json"
        self.wheelhouse.mkdir()
        core = _wheel(self.wheelhouse, "xrefkit", {
            "xrefkit/__init__.py": "",
            "xrefkit/__main__.py": "import sys\nfrom .cli import main\nmain(sys.argv[1:])\n",
            "xrefkit/cli.py": (
                "import fixturedep\nfrom . import operations_cli\n"
                "def main(args=None):\n"
                "    if args and args[0] == 'workflow': return operations_cli.main(args)\n"
                "    if args and args[0] == 'xref':\n"
                "        import json\n"
                "        print(json.dumps(dict(ok=True, xid=args[2], truncated=False, text='fixture startup')))\n"
                "        return 0\n"
                "    print(fixturedep.VALUE)\n"
            ),
            "xrefkit/operations_cli.py": (
                "def main(args):\n    print('usage: xrefkit workflow ' + args[1])\n    return 0\n"
            ),
            "xrefkit/execution_binding.py": (
                "BINDING_SCHEMA_VERSION = 1\ndef build_execution_binding(): pass\ndef validate_binding_context(): pass\n"
            ),
        }, "Requires-Dist: fixturedep==1.0\n")
        dep = _wheel(self.wheelhouse, "fixturedep", {"fixturedep.py": "VALUE = 'fixture Core ran'\n"})
        self.pins = {"schema": 1, "target": _target(), "packages": {
            "xrefkit": {"version": "1.0", "sha256": [core]},
            "fixturedep": {"version": "1.0", "sha256": [dep]},
        }}
        self.lock.write_text(json.dumps(self.pins), encoding="ascii")

    def launch(self, *args, interrupt=False):
        return subprocess.Popen(
            [sys.executable, "-I", "-B", "-c", _COMMAND, str(_SOURCE), "interrupt" if interrupt else "normal",
             "--lock", str(self.lock), "--cache-dir", str(self.cache), "--offline", *map(str, args)],
            cwd=self.temp.name, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env={**os.environ, "PIP_INDEX_URL": "https://127.0.0.1:1/"},
        )

    def finish(self, job, expected=0):
        try:
            stdout, stderr = job.communicate(timeout=150)
        finally:
            if job.poll() is None:
                job.kill()
                job.communicate()
        self.assertEqual(job.returncode, expected, stderr)
        return stdout.strip(), stderr

    def resolve(self, *args):
        return json.loads(self.finish(self.launch(*args))[0])

    def test_cold_concurrent_warm_local_and_invalidation(self):
        jobs = [self.launch("--wheelhouse", self.wheelhouse) for _ in range(2)]
        records = [json.loads(self.finish(job)[0]) for job in jobs]
        self.assertCountEqual([r["source"] for r in records], ["wheelhouse", "cache"])
        fresh = records[0]
        self.assertEqual(fresh["python"], records[1]["python"])
        self.assertEqual(self.resolve()["python"], fresh["python"])
        self.assertEqual(fresh["binding_schema_version"], 1)
        self.assertEqual(self.resolve("--local-python", fresh["python"])["source"], "local")
        self.assertEqual(self.finish(self.launch("--", "example"))[0], "fixture Core ran")

        site = next(Path(fresh["python"]).parent.parent.rglob("fixturedep.py"))
        site.write_text("raise RuntimeError('invalid cache')\n")
        rebuilt = self.resolve()
        self.assertNotEqual(rebuilt["python"], fresh["python"])
        self.assertEqual(rebuilt["wheel_generation"], fresh["wheel_generation"])
        launcher = Path(rebuilt["python"])
        with launcher.open("ab") as executable:
            executable.write(b"tamper")
        restored = self.resolve()
        self.assertNotEqual(restored["python"], rebuilt["python"])
        self.assertNotEqual(self.resolve("--refresh")["python"], restored["python"])
        self.assertTrue(Path(rebuilt["python"]).exists())

        self.lock.write_text(json.dumps(self.pins, indent=2), encoding="ascii")
        self.assertIn("offline cache miss", self.finish(self.launch(), expected=2)[1])

    def test_abrupt_exit_after_wheels_then_offline_recovery(self):
        self.finish(self.launch("--wheelhouse", self.wheelhouse, interrupt=True), expected=73)
        self.assertFalse(list(self.cache.rglob("ready.json")))
        recovered = self.resolve()
        self.assertNotEqual(recovered["generation"], recovered["wheel_generation"])
        self.assertEqual(self.resolve()["source"], "cache")

        artifact_root = Path(recovered["python"]).parents[3] / recovered["wheel_generation"] / "wheels"
        wheel = next(artifact_root.glob("xrefkit-*.whl"))
        wheel.write_bytes(b"corrupt")
        self.assertIn("offline cache miss", self.finish(self.launch(), expected=2)[1])
        self.assertEqual(self.resolve("--wheelhouse", self.wheelhouse)["source"], "wheelhouse")

    def test_desktop_stop_cancels_install_and_recovers_before_runtime_admission(self):
        root = Path(self.temp.name)
        journal = root / "desktop.sqlite"
        thread, turn, resumed_turn = (str(uuid4()) for _ in range(3))
        sessions = root / "sessions"
        sessions.mkdir()
        rollout = sessions / f"rollout-fixture-{thread}.jsonl"
        rollout.touch()
        trusted = root / "trusted" / "startup.md"
        trusted.parent.mkdir()
        trusted.write_bytes(b"<!-- xid: C3A1F78D9B22 -->\n# Reviewed contract\n")
        digest = hashlib.sha256(trusted.read_bytes()).hexdigest()
        (root / "startup.md").write_bytes(b"<!-- xid: C3A1F78D9B22 -->\n# Unreviewed contract\n")
        env = {**os.environ, "CODEX_THREAD_ID": thread, "CODEX_HOME": str(root),
               "LOCALAPPDATA": str(root)}
        env.pop("OPENAI_API_KEY", None)
        command = [sys.executable, "-I", "-B", "-c", _COMMAND, str(_SOURCE)]
        args = [
            "desktop", str(_SOURCE.parents[2]), "desktop-flow",
            "--journal", str(journal), "--core-lock", str(self.lock),
            "--core-cache-dir", str(self.cache), "--core-startup-file", str(trusted),
        ]

        def answer(turn_id):
            return json.dumps(dict(hostId="local", threadId=thread, turnId=turn_id, status="inProgress")) + "\n"

        def abort(turn_id):
            with rollout.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(type="event_msg", payload=dict(type="turn_aborted", turn_id=turn_id))) + "\n")

        def run(extra, replies):
            result = subprocess.run([*command, "normal", *args, *extra], cwd=root, env=env,
                                    input=replies, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 2, result.stderr)
            return list(map(json.loads, result.stdout.splitlines()))

        invalid = run(["--turn-id", turn, "--core-startup-sha256", "0" * 64], answer(turn))
        self.assertEqual(invalid[-1]["reason"], "core_startup_unavailable")
        self.assertFalse(self.cache.exists())

        with subprocess.Popen([*command, "desktop-stop", *args, "--turn-id", turn,
                               "--core-startup-sha256", digest, "--core-wheelhouse", str(self.wheelhouse)],
                              cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True) as job:
            try:
                job.stdin.write(answer(turn))
                job.stdin.flush()
                deadline = monotonic() + 90
                while not list(self.cache.rglob("installer.pid")) and job.poll() is None and monotonic() < deadline:
                    sleep(0.05)
                marker, = list(self.cache.rglob("installer.pid"))
                child_pid = int(marker.read_text())
                abort(str(uuid4()))
                sleep(0.3)
                self.assertIsNone(job.poll())
                abort(turn)
                stdout, stderr = job.communicate(timeout=15)
                self.assertEqual(job.returncode, 2, stderr)
                self.assertEqual(json.loads(stdout.splitlines()[-1])["reason"], "core_acquisition_stopped")
                self.assertTrue(_process_has_ended(child_pid))
            finally:
                if job.poll() is None:
                    job.kill()
                    job.communicate()
        self.assertFalse(journal.exists())
        self.assertFalse(list(self.cache.rglob("ready.json")))

        resumed = run(["--turn-id", resumed_turn, "--core-startup-sha256", digest], answer(resumed_turn))
        recovered, = [r for r in resumed if r["status"] == "core_runtime_ready"]
        self.assertEqual(recovered["source"], "wheelhouse")
        self.assertEqual(recovered["startup_sha256"], digest)
        self.assertEqual(resumed[-1]["reason"], "origin_unconfirmed_after_core_startup")
        warm = run(["--turn-id", resumed_turn, "--core-startup-sha256", digest], answer(resumed_turn))
        cached, = [r for r in warm if r["status"] == "core_runtime_ready"]
        self.assertEqual(cached, {**recovered, "source": "cache"})
        self.assertFalse(journal.exists())

    def test_offline_wheelhouse_ignores_html_links(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_error(404)

        (self.wheelhouse / "fixturedep-1.0-py3-none-any.whl").unlink()
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                (self.wheelhouse / "links.html").write_text(
                    f'<a href="http://127.0.0.1:{server.server_port}/fixturedep-1.0-py3-none-any.whl">wheel</a>'
                )
                _, stderr = self.finish(self.launch("--wheelhouse", self.wheelhouse), expected=2)
                self.assertIn("obtain compatible hash-pinned wheels", stderr)
                self.assertEqual(requests, [])
            finally:
                server.shutdown()
                worker.join()

    def test_missing_workflow_interface_cannot_be_published(self):
        wheel = self.wheelhouse / "xrefkit-1.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel) as source:
            files = {item: source.read(item) for item in source.namelist() if ".dist-info/" not in item}
        files.pop("xrefkit/operations_cli.py")
        self.pins["packages"]["xrefkit"]["sha256"] = [
            _wheel(self.wheelhouse, "xrefkit", files, "Requires-Dist: fixturedep==1.0\n")
        ]
        self.lock.write_text(json.dumps(self.pins), encoding="ascii")
        _, stderr = self.finish(self.launch("--wheelhouse", self.wheelhouse), expected=2)
        self.assertIn("Core identity/interface check", stderr)
        self.assertFalse(list(self.cache.rglob("ready.json")))

    def test_bootstrap_packages_cannot_satisfy_unlocked_runtime_dependencies(self):
        wheel = self.wheelhouse / "fixturedep-1.0-py3-none-any.whl"
        original = wheel.read_bytes()
        with zipfile.ZipFile(wheel) as source:
            files = {item: source.read(item) for item in source.namelist() if ".dist-info/" not in item}
        self.pins["packages"]["fixturedep"]["sha256"] = [
            _wheel(self.wheelhouse, "fixturedep", files, "Requires-Dist: pip\n")
        ]
        self.assertNotEqual(wheel.read_bytes(), original)
        self.lock.write_text(json.dumps(self.pins), encoding="ascii")
        _, stderr = self.finish(self.launch("--wheelhouse", self.wheelhouse), expected=2)
        self.assertIn("check installed dependencies", stderr)
        self.assertFalse(list(self.cache.rglob("ready.json")))

    def test_bad_hash_and_target_refuse_before_use(self):
        self.pins["packages"]["xrefkit"]["sha256"] = ["0" * 64]
        self.lock.write_text(json.dumps(self.pins), encoding="ascii")
        self.assertIn("hash-pinned wheels", self.finish(self.launch("--wheelhouse", self.wheelhouse), 2)[1])
        self.assertFalse(list(self.cache.rglob("ready.json")))
        self.pins["target"] = "unsupported"
        self.lock.write_text(json.dumps(self.pins), encoding="ascii")
        self.assertIn("unsupported", self.finish(self.launch(), 2)[1])


if __name__ == "__main__":
    unittest.main()
