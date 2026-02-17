import os
import sys
import types
import json
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def monkeypatch_env(monkeypatch):
    class EnvPatcher:
        def set(self, key, value):
            monkeypatch.setenv(key, str(value))
        def delete(self, key):
            monkeypatch.delenv(key, raising=False)
        def clear_prefix(self, prefix):
            for k in list(os.environ.keys()):
                if k.startswith(prefix):
                    monkeypatch.delenv(k, raising=False)
    return EnvPatcher()


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp(prefix="pwr-tests-")
    try:
        yield Path(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_numbers():
    return [1.0, 2.0, 3.0, 4.0, 5.0]


@pytest.fixture
def sample_series_irregular():
    # data with outliers and irregular distribution for analytics
    return [0.1, 0.2, 0.25, 10.0, 0.3, 0.28, 0.27]


@pytest.fixture
def fake_subprocess_run(monkeypatch):
    calls = []

    class Result:
        def __init__(self, returncode=0, stdout=b"", stderr=b""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def _run(cmd, *args, **kwargs):
        calls.append({"cmd": cmd, "args": args, "kwargs": kwargs})
        return Result(0, b"ok", b"")

    try:
        import subprocess
        monkeypatch.setattr(subprocess, "run", _run)
    except Exception:
        pass

    return calls


@pytest.fixture(autouse=True)
def ensure_pkg_on_path():
    # Ensure local package import works in tests when running from repo root
    root = Path(__file__).resolve().parents[1]
    pkg = root / "power_benchmarking_suite"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    assert pkg.exists(), "Expected power_benchmarking_suite package to exist"


@pytest.fixture
def write_json(tmp_dir):
    def _write(name, data):
        p = tmp_dir / name
        p.write_text(json.dumps(data))
        return p
    return _write
