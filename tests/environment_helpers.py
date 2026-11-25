"""Explicit environment mocks for tests that do not launch configured children."""
from contextlib import contextmanager
import os
from unittest.mock import patch


@contextmanager
def mock_environment(values, *, clear=False):
    """Change Python lookups without clearing/restoring the native environment.

    On Windows, restoring an inherited empty value through os._Environ can
    remove it from the native child environment even though the Python mapping
    still contains it. These unit tests only need controlled credential lookups.
    Tests configuring a subprocess must pass its explicit ``env`` separately.
    """
    replacement = {} if clear else dict(os.environ)
    replacement.update(values)
    with patch.object(os, "environ", replacement):
        yield replacement
