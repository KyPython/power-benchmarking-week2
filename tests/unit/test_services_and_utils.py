import importlib
from pathlib import Path
import json
import os
import pytest


docgen = importlib.import_module("power_benchmarking_suite.services.document_generator")
pdfgen = importlib.import_module("power_benchmarking_suite.services.pdf_generator")
storage = importlib.import_module("power_benchmarking_suite.services.storage")
errutil = importlib.import_module("power_benchmarking_suite.utils.error_handler")


@pytest.mark.unit
def test_document_generator_html(tmp_path):
    gen = docgen.DocumentGenerator(output_dir=str(tmp_path))
    out = gen.generate_html_report("Test Report", "<p>Hello</p>")
    assert out is not None and Path(out).exists()
    text = Path(out).read_text()
    assert "Test Report" in text and "<p>Hello</p>" in text


@pytest.mark.unit
def test_storage_crud(tmp_path):
    svc = storage.StorageService(storage_path=str(tmp_path))
    item = svc.create("clients", {"name": "Acme"})
    assert "id" in item
    got = svc.get("clients", item["id"])
    assert got is not None and got["name"] == "Acme"
    updated = svc.update("clients", item["id"], {"name": "New"})
    assert updated and updated["name"] == "New"
    ok = svc.delete("clients", item["id"])
    assert ok is True


@pytest.mark.unit
def test_error_utils_check_powermetrics_availability(monkeypatch):
    # Simulate missing powermetrics and sudo
    def fake_run(args, capture_output=True, text=True, timeout=2, check=False):
        class R:
            def __init__(self, returncode=0, stdout=""):
                self.returncode = returncode
                self.stdout = stdout
        cmd = args[0]
        if args[:2] == ["which", "powermetrics"]:
            return R(returncode=1, stdout="")
        if args[:1] == ["which"] and args[1] == "sudo":
            return R(returncode=1, stdout="")
        return R(0, "/usr/bin/which")

    import subprocess
    monkeypatch.setattr(subprocess, "run", fake_run)

    is_avail, err = errutil.check_powermetrics_availability()
    assert is_avail is False
    assert err is not None


@pytest.mark.unit
def test_check_sudo_permissions_root(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    ok, msg = errutil.check_sudo_permissions("powermetrics")
    assert ok is True and msg is None
