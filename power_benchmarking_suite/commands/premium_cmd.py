#!/usr/bin/env python3
"""
Premium Command - Simple premium subscription management

Usage:
    power-benchmark premium           # Check status & upgrade if needed
    power-benchmark premium status   # Show current status
    power-benchmark premium upgrade  # Open checkout
    power-benchmark premium login    # Activate (after purchase)
    power-benchmark premium test    # Try premium for free
"""

import argparse
import json
from pathlib import Path
import logging
import os
import webbrowser
import time
import requests

logger = logging.getLogger(__name__)

PREMIUM_CONFIG_FILE = Path.home() / ".power_benchmarking" / "premium_config.json"


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add premium command to argument parser."""
    parser = subparsers.add_parser(
        "premium",
        help="Manage premium subscription",
        description="Simple premium management: status, upgrade, login",
    )
    sub = parser.add_subparsers(dest="premium_action", help="Action")

    # Main command - just show status
    p_status = sub.add_parser("status", help="Show premium status")
    p_status.set_defaults(premium_action="status")

    # Upgrade - open checkout
    p_upgrade = sub.add_parser("upgrade", help="Open checkout to upgrade")
    p_upgrade.add_argument("--open", action="store_true", help="Open in browser")
    p_upgrade.set_defaults(premium_action="upgrade")

    # Login - activate after purchase  
    p_login = sub.add_parser("login", help="Activate premium (after purchase)")
    p_login.add_argument("--code", help="Activation code from email/web")
    p_login.set_defaults(premium_action="login")

    # Test - try premium
    p_test = sub.add_parser("test", help="Try premium features (local only)")
    p_test.set_defaults(premium_action="test")

    # Verify - force check with Polar
    p_verify = sub.add_parser("verify", help="Verify with Polar (force refresh)")
    p_verify.set_defaults(premium_action="verify")

    parser.set_defaults(func=run)
    return parser


def _read_status():
    """Read premium status from config."""
    if PREMIUM_CONFIG_FILE.exists():
        try:
            return json.loads(PREMIUM_CONFIG_FILE.read_text())
        except Exception:
            pass
    return {"tier": "free", "features": {}}


def _write_status(data: dict):
    """Write premium status to config."""
    PREMIUM_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREMIUM_CONFIG_FILE.write_text(json.dumps(data, indent=2))


def _get_checkout_url():
    """Get checkout URL from Polar API or fallback."""
    polar_token = os.getenv("POLAR_ACCESS_TOKEN")
    
    if polar_token and requests:
        try:
            headers = {"Authorization": f"Bearer {polar_token}", "Accept": "application/json"}
            
            # Try to get products and create checkout
            resp = requests.get("https://api.polar.sh/v1/products", headers=headers, timeout=10)
            if resp.status_code == 200:
                products = resp.json().get("items", [])
                for p in products:
                    prices = p.get("prices", [])
                    if prices:
                        price_id = prices[0].get("id")
                        # Create checkout
                        checkout = requests.post(
                            "https://api.polar.sh/v1/checkouts",
                            headers=headers,
                            json={"price_id": price_id},
                            timeout=10
                        )
                        if checkout.status_code in (200, 201):
                            url = checkout.json().get("url")
                            if url:
                                return url
        except Exception:
            pass
    
    # Fallback to pricing page
    base = os.getenv("NEXT_PUBLIC_BASE_URL", "https://power-benchmarking-week2.vercel.app")
    return f"{base}/pricing"


def run(args: argparse.Namespace, config=None) -> int:
    action = getattr(args, "premium_action", None)
    
    # Default: show status (if no action specified)
    if action is None:
        action = "status"
    
    # STATUS - Show current tier
    if action == "status":
        status = _read_status()
        tier = status.get("tier", "free")
        
        print("\n💎 PREMIUM STATUS")
        print(f"   Tier: {tier.upper()}")
        
        if tier == "premium":
            features = status.get("features", {})
            if features:
                print("\n   Features enabled:")
                for name, enabled in features.items():
                    if enabled:
                        icon = "✓"
                        label = name.replace("_", " ").title()
                        print(f"     {icon} {label}")
            
            ver = status.get("verification", {})
            if ver.get("verified_at"):
                print(f"\n   Verified: {ver['verified_at'][:10]}")
        else:
            print("\n   Upgrade to unlock:")
            print("     • Unlimited monitoring sessions")
            print("     • Advanced analytics")
            print("\n   Run: power-benchmark premium upgrade")
        
        print()
        return 0
    
    # UPgrade - Open checkout
    elif action == "upgrade":
        print("\n🚀 UPGRADING TO PREMIUM...")
        
        url = _get_checkout_url()
        print(f"\n   Opening: {url}")
        
        if getattr(args, "open", True):
            try:
                webbrowser.open(url)
                print("   ✓ Opened in browser")
            except Exception:
                pass
        
        print("\n   After purchase, run:")
        print("   → power-benchmark premium login")
        print()
        return 0
    
    # LOGIN - Activate after purchase
    elif action == "login":
        code = getattr(args, "code", None)
        
        if code:
            # User has a code - poll for activation
            return _poll_activation(code)
        else:
            # No code - show instructions
            print("\n🔐 ACTIVATING PREMIUM")
            print("\n   After completing purchase, you'll get an activation code.")
            print("   Run this command with your code:")
            print("\n   → power-benchmark premium login --code YOUR-CODE")
            print("\n   Or check your email for an activation link.")
            print()
            return 0
    
    # TEST - Try premium locally
    elif action == "test":
        data = {
            "tier": "premium",
            "features": {
                "unlimited_sessions": True,
                "advanced_analytics": True,
            },
            "test_mode": True,
        }
        _write_status(data)
        print("\n✅ Premium test mode enabled!")
        print("   (This is local only - not a real subscription)")
        print()
        return 0
    
    # VERIFY - Force check with Polar
    elif action == "verify":
        print("\n🔄 Verifying with Polar...")
        
        try:
            from power_benchmarking_suite.premium import PremiumFeatures
            pf = PremiumFeatures()
            ok = pf.verify_polar_entitlement()
            
            if ok:
                print("   ✓ Premium verified!")
            else:
                print("   ✗ Not verified - may need to upgrade")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print()
        return 0
    
    else:
        print("Usage: power-benchmark premium [status|upgrade|login|test|verify]")
        return 1


def _poll_activation(code: str) -> int:
    """Poll for device activation."""
    base_url = os.getenv("POWER_BENCHMARK_API_URL", "http://localhost:3000")
    code = code.upper()
    
    print(f"\n⏳ Waiting for activation of {code}...")
    print(f"   Or visit: {base_url}/activate?code={code}")
    
    for _ in range(20):  # 1 minute max
        time.sleep(3)
        try:
            resp = requests.get(f"{base_url}/api/device-codes/{code}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("activated") and data.get("token"):
                    # Save token
                    status = _read_status()
                    status["tier"] = "premium"
                    status["features"] = {
                        "unlimited_sessions": True,
                        "advanced_analytics": True,
                    }
                    status["licensing"] = {"polar_token": data["token"]}
                    _write_status(status)
                    
                    print("\n✅ Premium activated!")
                    return 0
        except Exception:
            pass
        print(".", end="", flush=True)
    
    print("\n\n⏱️ Timeout - code expired or invalid")
    return 1
