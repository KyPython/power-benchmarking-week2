#!/usr/bin/env python3
"""
Premium Command - Manage subscription status

Usage:
    power-benchmark premium status
    power-benchmark premium enable-test
    power-benchmark premium login --token <TOKEN>
    power-benchmark premium verify
    power-benchmark premium upgrade [--open] [--url <CHECKOUT_URL>]
"""

import argparse
import json
from pathlib import Path
import logging
import os
import webbrowser

logger = logging.getLogger(__name__)

PREMIUM_CONFIG_FILE = Path.home() / ".power_benchmarking" / "premium_config.json"


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add premium command to argument parser."""
    parser = subparsers.add_parser(
        "premium",
        help="Manage premium subscription",
        description="Check status, enable test mode, and get upgrade instructions",
    )
    sub = parser.add_subparsers(dest="premium_action", help="Action")

    p_status = sub.add_parser("status", help="Show premium status")
    p_status.set_defaults(premium_action="status")

    p_enable = sub.add_parser("enable-test", help="Enable local premium test mode")
    p_enable.set_defaults(premium_action="enable-test")

    p_login = sub.add_parser("login", help="Store Polar license token locally")
    p_login.add_argument("--token", required=True, help="Polar license token")
    p_login.set_defaults(premium_action="login")

    p_verify = sub.add_parser("verify", help="Verify entitlement via Polar API")
    p_verify.set_defaults(premium_action="verify")

    p_upgrade = sub.add_parser("upgrade", help="Show upgrade instructions / open checkout")
    p_upgrade.add_argument("--open", action="store_true", help="Open checkout/pricing URL in browser")
    p_upgrade.add_argument("--url", help="Checkout/pricing URL to open")
    p_upgrade.set_defaults(premium_action="upgrade")

    parser.set_defaults(func=run)
    return parser


def _read_status():
    if PREMIUM_CONFIG_FILE.exists():
        try:
            return json.loads(PREMIUM_CONFIG_FILE.read_text())
        except Exception:
            pass
    return {"tier": "free", "features": {}}


def _write_status(data: dict):
    PREMIUM_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREMIUM_CONFIG_FILE.write_text(json.dumps(data, indent=2))


def run(args: argparse.Namespace, config=None) -> int:
    action = getattr(args, "premium_action", None)
    if action == "status":
        status = _read_status()
        tier = status.get("tier", "free")
        print("\n💎 PREMIUM STATUS")
        print(f"Tier: {tier.upper()}")
        if tier == "premium":
            print("Features:")
            for k, v in (status.get("features") or {}).items():
                print(f"  - {k}: {'ENABLED' if v else 'DISABLED'}")
        else:
            print("Free tier limits: 1 device, 1 hour/session, basic analytics")
            print("Upgrade: power-benchmark premium upgrade --open")
        return 0
    elif action == "enable-test":
        data = {
            "tier": "premium",
            "features": {
                "cloud_sync": True,
                "team_collaboration": True,
                "advanced_analytics": True,
            },
        }
        _write_status(data)
        print("✅ Premium test mode enabled locally (not billed)")
        return 0
    elif action == "login":
        # Store token in premium config (no network verification in OSS)
        status = _read_status()
        status.setdefault("licensing", {})["polar_token"] = getattr(args, "token")
        _write_status(status)
        print("✅ Polar token stored locally")
        return 0
    elif action == "verify":
        # Call into premium module for verification
        try:
            from power_benchmarking_suite.premium import PremiumFeatures
            pf = PremiumFeatures()
            ok = pf.verify_polar_entitlement()
            if ok:
                print("✅ Entitlement verified via Polar; premium features enabled")
                return 0
            else:
                print("⚠️ Verification failed; using local tier settings")
                return 1
        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return 1
    elif action == "upgrade":
        # Prefer explicit URL, then config, then env
        status = _read_status()
        lic = (status or {}).get("licensing") or {}
        url = getattr(args, "url", None) or lic.get("checkout_url") or os.getenv("POLAR_CHECKOUT_URL") or os.getenv("POLAR_PRICING_URL")
        print("Upgrade via Polar/Stripe:")
        print("  - Complete checkout to enable premium")
        if url:
            print(f"  - Checkout URL: {url}")
            if getattr(args, "open", False):
                try:
                    webbrowser.open(url)
                    print("🌐 Opening browser to checkout…")
                except Exception:
                    print("⚠️ Unable to open browser; copy the URL above")
        else:
            print("  - Provide a URL with --url or set POLAR_CHECKOUT_URL/POLAR_PRICING_URL")
        print("After purchase:")
        print("  power-benchmark premium login --token <polar_oat_…> && power-benchmark premium verify")
        return 0
    else:
        print("Specify an action: status | enable-test | login | verify | upgrade")
        return 1
