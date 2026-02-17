#!/usr/bin/env python3
"""
Usage Tracking

Tracks per-session usage locally for pricing enforcement and analytics.
Stored at ~/.power_benchmarking/usage.json
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

USAGE_FILE = Path.home() / ".power_benchmarking" / "usage.json"


def _load() -> Dict[str, Any]:
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text())
        except Exception:
            pass
    return {"days": {}}


def _save(data: Dict[str, Any]):
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(data, indent=2))


def record_session(command: str, seconds: int, success: bool = True):
    """Record a usage session."""
    data = _load()
    day = datetime.utcnow().strftime("%Y-%m-%d")
    days = data.setdefault("days", {})
    entry = days.setdefault(day, {"total_seconds": 0, "sessions": []})
    entry["total_seconds"] = int(entry.get("total_seconds", 0)) + int(max(0, seconds))
    entry["sessions"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "command": command,
        "seconds": int(max(0, seconds)),
        "success": bool(success),
    })
    _save(data)


def usage_summary() -> Dict[str, Any]:
    """Get simple usage summary (today + totals)."""
    data = _load()
    day = datetime.utcnow().strftime("%Y-%m-%d")
    today = data.get("days", {}).get(day, {"total_seconds": 0, "sessions": []})
    total = 0
    for d in data.get("days", {}).values():
        total += int(d.get("total_seconds", 0))
    return {
        "today_seconds": int(today.get("total_seconds", 0)),
        "today_sessions": len(today.get("sessions", [])),
        "total_seconds": int(total),
        "days_tracked": len(data.get("days", {})),
    }
