import importlib
import signal
import time
import pytest

esh = importlib.import_module("scripts.enhanced_signal_handler")


@pytest.mark.unit
def test_handler_lifecycle(monkeypatch):
    # Avoid registering real OS signal handlers by faking signal.signal
    original_signal = signal.signal
    calls = []

    def fake_signal(sig, handler):
        calls.append((sig, handler))
        return original_signal

    monkeypatch.setattr(signal, "signal", fake_signal)

    received = {}

    def cb(sig, name):
        received["sig"] = sig
        received["name"] = name

    handler = esh.EnhancedSignalHandler(shutdown_callback=cb)

    # Simulate receiving SIGINT by invoking the private handler directly
    handler._handle_signal(signal.SIGINT, None)
    assert esh.is_shutdown_requested() or handler.is_running() is False
    info = handler.get_signal_info()
    assert info is None or info.get("name")
