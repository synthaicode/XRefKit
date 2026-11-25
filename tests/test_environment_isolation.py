import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class EnvironmentMockIsolationTests(unittest.TestCase):
    def test_inherited_empty_native_value_survives_mock_and_exception(self):
        # Pass the empty value when creating the child: assigning it through
        # os.environ inside the child cannot reproduce this Windows condition.
        environment = dict(os.environ)
        environment["XREFKIT_TEST_EMPTY_NATIVE_VALUE"] = ""
        environment.pop("XREFKIT_TEST_MOCK_ONLY_VALUE", None)
        script = r'''
import json
import os
import subprocess
import sys
from environment_helpers import mock_environment

key = "XREFKIT_TEST_EMPTY_NATIVE_VALUE"
mock_key = "XREFKIT_TEST_MOCK_ONLY_VALUE"
original = os.environ
probe = "import json,os; print(json.dumps([os.environ.get('XREFKIT_TEST_EMPTY_NATIVE_VALUE') == '', 'XREFKIT_TEST_MOCK_ONLY_VALUE' in os.environ]))"
def native_state():
    # Deliberately omit env: probe the actual inherited native environment,
    # not a reconstruction from Python's possibly divergent os.environ.
    result = subprocess.run([sys.executable, "-c", probe], check=True,
                            capture_output=True, text=True, timeout=20)
    return json.loads(result.stdout)

states = [native_state()]
with mock_environment({mock_key: "synthetic"}):
    assert os.environ[key] == "" and os.environ[mock_key] == "synthetic"
    states.append(native_state())
assert os.environ is original
states.append(native_state())
try:
    with mock_environment({mock_key: "synthetic"}, clear=True):
        assert key not in os.environ and os.environ[mock_key] == "synthetic"
        states.append(native_state())
        raise RuntimeError("synthetic test exit")
except RuntimeError:
    pass
assert os.environ is original
states.append(native_state())
print(json.dumps(states))
'''
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=Path(__file__).resolve().parent,
            env=environment, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # Only two booleans are reported; no inherited environment values leak.
        self.assertEqual(json.loads(result.stdout), [[True, False]] * 5)


if __name__ == "__main__":
    unittest.main()
