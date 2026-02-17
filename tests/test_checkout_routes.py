#!/usr/bin/env python3
"""
Sanity tests for Polar checkout routes in repo.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_checkout_route_exists():
    # We now use a custom checkout handler that calls Polar's REST API,
    # not the @polar-sh/nextjs helper, but the route file must still exist.
    path = REPO_ROOT / "app" / "api" / "checkout" / "route.js"
    assert path.exists(), f"Missing checkout route: {path}"


def test_success_page_exists():
    path = REPO_ROOT / "app" / "success" / "page.js"
    assert path.exists(), f"Missing success page: {path}"


def test_package_has_next_dep():
    pkg = json.loads((REPO_ROOT / "package.json").read_text())
    deps = pkg.get("dependencies", {})
    assert "next" in deps
