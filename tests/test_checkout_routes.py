#!/usr/bin/env python3
"""
Sanity tests for Polar checkout routes in repo.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_checkout_route_exists():
    path = REPO_ROOT / "app" / "api" / "checkout" / "route.js"
    assert path.exists(), f"Missing checkout route: {path}"
    content = path.read_text()
    assert "Checkout({" in content


def test_success_page_exists():
    path = REPO_ROOT / "app" / "success" / "page.js"
    assert path.exists(), f"Missing success page: {path}"


def test_package_has_polar_dep():
    pkg = json.loads((REPO_ROOT / "package.json").read_text())
    deps = pkg.get("dependencies", {})
    assert "@polar-sh/nextjs" in deps
