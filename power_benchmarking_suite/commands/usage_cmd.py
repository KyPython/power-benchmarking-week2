#!/usr/bin/env python3
"""
Usage Command - Show local usage stats

Usage:
    power-benchmark usage summary
"""
import argparse
from typing import Optional
from ..usage import usage_summary


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "usage",
        help="Show local usage stats",
        description="Display today's usage and total tracked seconds",
    )
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    s = usage_summary()
    print("\n📈 USAGE SUMMARY")
    print(f"Today: {s['today_sessions']} session(s), {s['today_seconds']} seconds")
    print(f"Total: {s['total_seconds']} seconds across {s['days_tracked']} day(s)")
    return 0
