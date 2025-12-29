#!/usr/bin/env python3
"""
Schedule Command - Automate command execution

Usage:
    power-benchmark schedule add --command "validate --verbose" --daily
    power-benchmark schedule add --command "monitor --test 30" --weekly
    power-benchmark schedule list
    power-benchmark schedule remove --id 1
    power-benchmark schedule run --id 1
"""

import argparse
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Configuration directory
CONFIG_DIR = Path.home() / ".power_benchmarking"
SCHEDULES_FILE = CONFIG_DIR / "schedules.json"
CONFIG_DIR.mkdir(exist_ok=True)


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add schedule command to argument parser."""
    parser = subparsers.add_parser(
        "schedule",
        aliases=["auto", "cron"],
        help="Schedule automated command execution",
        description="Schedule commands to run automatically at specified intervals",
    )

    subparsers_sched = parser.add_subparsers(dest="schedule_action", help="Schedule operation")

    # Add schedule
    parser_add = subparsers_sched.add_parser(
        "add",
        help="Add a new scheduled task",
        description="Schedule a command to run automatically",
    )
    parser_add.add_argument(
        "--command",
        type=str,
        required=True,
        help="Command to schedule (e.g., 'validate --verbose' or 'monitor --test 30')",
    )
    parser_add.add_argument(
        "--name",
        type=str,
        help="Friendly name for this schedule (default: auto-generated)",
    )
    parser_add.add_argument(
        "--daily",
        action="store_true",
        help="Run daily at 9 AM",
    )
    parser_add.add_argument(
        "--weekly",
        action="store_true",
        help="Run weekly on Monday at 9 AM",
    )
    parser_add.add_argument(
        "--hourly",
        action="store_true",
        help="Run every hour",
    )
    parser_add.add_argument(
        "--at",
        type=str,
        help="Run at specific time (HH:MM format, e.g., '14:30')",
    )
    parser_add.add_argument(
        "--interval",
        type=int,
        help="Run every N minutes",
    )
    parser_add.add_argument(
        "--enabled",
        action="store_true",
        default=True,
        help="Enable schedule immediately (default: True)",
    )
    parser_add.set_defaults(schedule_subtype="add")

    # List schedules
    parser_list = subparsers_sched.add_parser(
        "list",
        help="List all scheduled tasks",
        description="Show all configured scheduled tasks",
    )
    parser_list.add_argument(
        "--all",
        action="store_true",
        help="Show disabled schedules too",
    )
    parser_list.set_defaults(schedule_subtype="list")

    # Remove schedule
    parser_remove = subparsers_sched.add_parser(
        "remove",
        help="Remove a scheduled task",
        description="Remove a scheduled task by ID",
    )
    parser_remove.add_argument(
        "--id",
        type=int,
        required=True,
        help="Schedule ID to remove",
    )
    parser_remove.set_defaults(schedule_subtype="remove")

    # Enable/Disable schedule
    parser_toggle = subparsers_sched.add_parser(
        "toggle",
        help="Enable or disable a scheduled task",
        description="Enable or disable a scheduled task",
    )
    parser_toggle.add_argument(
        "--id",
        type=int,
        required=True,
        help="Schedule ID to toggle",
    )
    parser_toggle.set_defaults(schedule_subtype="toggle")

    # Run schedule now
    parser_run = subparsers_sched.add_parser(
        "run",
        help="Run a scheduled task now",
        description="Execute a scheduled task immediately",
    )
    parser_run.add_argument(
        "--id",
        type=int,
        required=True,
        help="Schedule ID to run",
    )
    parser_run.set_defaults(schedule_subtype="run")

    # Quick setup for common automations
    parser_setup = subparsers_sched.add_parser(
        "setup",
        help="Quick setup for common automations",
        description="Set up common automated tasks with one command",
    )
    parser_setup.add_argument(
        "--health-check",
        action="store_true",
        help="Set up daily system health check (validate --verbose)",
    )
    parser_setup.add_argument(
        "--power-monitor",
        action="store_true",
        help="Set up weekly power monitoring session",
    )
    parser_setup.add_argument(
        "--all",
        action="store_true",
        help="Set up all common automations",
    )
    parser_setup.set_defaults(schedule_subtype="setup")

    parser.set_defaults(func=run)
    return parser


def _load_schedules() -> List[Dict]:
    """Load schedules from file."""
    if not SCHEDULES_FILE.exists():
        return []
    try:
        with open(SCHEDULES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load schedules: {e}")
        return []


def _save_schedules(schedules: List[Dict]) -> None:
    """Save schedules to file."""
    try:
        with open(SCHEDULES_FILE, "w") as f:
            json.dump(schedules, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save schedules: {e}")
        raise


def _get_next_id(schedules: List[Dict]) -> int:
    """Get next available schedule ID."""
    if not schedules:
        return 1
    return max(s.get("id", 0) for s in schedules) + 1


def _parse_schedule(args: argparse.Namespace) -> Dict:
    """Parse schedule arguments into schedule dict."""
    schedule = {
        "command": args.command,
        "enabled": args.enabled,
        "created_at": datetime.now().isoformat(),
    }

    if args.name:
        schedule["name"] = args.name
    else:
        # Auto-generate name from command
        schedule["name"] = args.command.split()[0] if args.command else "Scheduled Task"

    # Parse timing
    if args.daily:
        schedule["type"] = "daily"
        schedule["time"] = args.at or "09:00"
    elif args.weekly:
        schedule["type"] = "weekly"
        schedule["day"] = "monday"
        schedule["time"] = args.at or "09:00"
    elif args.hourly:
        schedule["type"] = "hourly"
    elif args.interval:
        schedule["type"] = "interval"
        schedule["minutes"] = args.interval
    elif args.at:
        schedule["type"] = "daily"
        schedule["time"] = args.at
    else:
        # Default to daily at 9 AM
        schedule["type"] = "daily"
        schedule["time"] = "09:00"

    return schedule


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute schedule command."""
    try:
        if not hasattr(args, "schedule_action") or args.schedule_action is None:
            logger.error("Schedule action required. Use 'add', 'list', 'remove', 'toggle', 'run', or 'setup'")
            return 1

        if args.schedule_action == "add":
            return _handle_add(args, config)
        elif args.schedule_action == "list":
            return _handle_list(args, config)
        elif args.schedule_action == "remove":
            return _handle_remove(args, config)
        elif args.schedule_action == "toggle":
            return _handle_toggle(args, config)
        elif args.schedule_action == "run":
            return _handle_run(args, config)
        elif args.schedule_action == "setup":
            return _handle_setup(args, config)
        else:
            logger.error(f"Unknown schedule action: {args.schedule_action}")
            return 1

    except Exception as e:
        logger.error(f"Schedule command failed: {e}", exc_info=True)
        return 1


def _handle_add(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle add schedule."""
    schedules = _load_schedules()
    schedule = _parse_schedule(args)
    schedule["id"] = _get_next_id(schedules)
    schedules.append(schedule)
    _save_schedules(schedules)

    print(f"\n✅ Schedule added:")
    print(f"  ID: {schedule['id']}")
    print(f"  Name: {schedule['name']}")
    print(f"  Command: {schedule['command']}")
    print(f"  Type: {schedule['type']}")
    if schedule['type'] == 'daily' or schedule['type'] == 'weekly':
        print(f"  Time: {schedule.get('time', 'N/A')}")
    if schedule['type'] == 'interval':
        print(f"  Interval: Every {schedule.get('minutes')} minutes")
    print(f"  Status: {'Enabled' if schedule['enabled'] else 'Disabled'}")
    print()
    print("💡 To enable system-level scheduling, run:")
    print("   power-benchmark schedule setup --all")
    print()

    return 0


def _handle_list(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle list schedules."""
    schedules = _load_schedules()

    if not schedules:
        print("\n📅 No scheduled tasks configured.")
        print("   Use 'power-benchmark schedule add' to create one.")
        print()
        return 0

    enabled_schedules = [s for s in schedules if s.get("enabled", True)]
    disabled_schedules = [s for s in schedules if not s.get("enabled", True)]

    print("\n📅 Scheduled Tasks:")
    print("=" * 70)

    if enabled_schedules:
        print("\n✅ Enabled:")
        for schedule in enabled_schedules:
            print(f"\n  ID: {schedule.get('id')}")
            print(f"  Name: {schedule.get('name', 'Unnamed')}")
            print(f"  Command: {schedule.get('command')}")
            print(f"  Type: {schedule.get('type', 'unknown')}")
            if schedule.get('type') in ['daily', 'weekly']:
                print(f"  Time: {schedule.get('time', 'N/A')}")
            if schedule.get('type') == 'interval':
                print(f"  Interval: Every {schedule.get('minutes')} minutes")
            if schedule.get('created_at'):
                created = datetime.fromisoformat(schedule['created_at'])
                print(f"  Created: {created.strftime('%Y-%m-%d %H:%M')}")

    if args.all and disabled_schedules:
        print("\n❌ Disabled:")
        for schedule in disabled_schedules:
            print(f"\n  ID: {schedule.get('id')}")
            print(f"  Name: {schedule.get('name', 'Unnamed')}")
            print(f"  Command: {schedule.get('command')}")
            print(f"  Status: Disabled")

    print()
    print("💡 Commands:")
    print("   power-benchmark schedule run --id <ID>    # Run now")
    print("   power-benchmark schedule toggle --id <ID> # Enable/disable")
    print("   power-benchmark schedule remove --id <ID> # Remove")
    print()

    return 0


def _handle_remove(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle remove schedule."""
    schedules = _load_schedules()
    original_count = len(schedules)
    schedules = [s for s in schedules if s.get("id") != args.id]
    _save_schedules(schedules)

    if len(schedules) < original_count:
        print(f"\n✅ Schedule {args.id} removed")
        print()
        return 0
    else:
        print(f"\n❌ Schedule {args.id} not found")
        print()
        return 1


def _handle_toggle(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle toggle schedule."""
    schedules = _load_schedules()
    for schedule in schedules:
        if schedule.get("id") == args.id:
            schedule["enabled"] = not schedule.get("enabled", True)
            _save_schedules(schedules)
            status = "enabled" if schedule["enabled"] else "disabled"
            print(f"\n✅ Schedule {args.id} {status}")
            print()
            return 0

    print(f"\n❌ Schedule {args.id} not found")
    print()
    return 1


def _handle_run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle run schedule now."""
    schedules = _load_schedules()
    for schedule in schedules:
        if schedule.get("id") == args.id:
            command = schedule.get("command", "")
            if not command:
                print(f"\n❌ Schedule {args.id} has no command")
                return 1

            print(f"\n🚀 Running scheduled task: {schedule.get('name', 'Unnamed')}")
            print(f"   Command: {command}")
            print()

            # Execute the command
            try:
                # Split command into parts
                cmd_parts = command.split()
                if cmd_parts[0] == "power-benchmark":
                    cmd_parts = cmd_parts[1:]
                elif cmd_parts[0].startswith("power-benchmark"):
                    cmd_parts = cmd_parts[0].split()[1:] + cmd_parts[1:]

                # Build full command
                full_cmd = ["power-benchmark"] + cmd_parts

                result = subprocess.run(full_cmd, check=False)
                return result.returncode
            except Exception as e:
                logger.error(f"Failed to run scheduled command: {e}")
                print(f"❌ Error running command: {e}")
                return 1

    print(f"\n❌ Schedule {args.id} not found")
    print()
    return 1


def _handle_setup(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Handle quick setup for common automations."""
    schedules = _load_schedules()
    added_count = 0

    if args.all or args.health_check:
        # Daily system health check
        schedule = {
            "id": _get_next_id(schedules),
            "name": "Daily System Health Check",
            "command": "validate --verbose",
            "type": "daily",
            "time": "09:00",
            "enabled": True,
            "created_at": datetime.now().isoformat(),
        }
        schedules.append(schedule)
        added_count += 1
        print("✅ Added: Daily System Health Check (validate --verbose at 9 AM)")

    if args.all or args.power_monitor:
        # Weekly power monitoring
        schedule = {
            "id": _get_next_id(schedules),
            "name": "Weekly Power Monitoring",
            "command": "monitor --test 300 --output weekly_power_log.csv",
            "type": "weekly",
            "day": "monday",
            "time": "10:00",
            "enabled": True,
            "created_at": datetime.now().isoformat(),
        }
        schedules.append(schedule)
        added_count += 1
        print("✅ Added: Weekly Power Monitoring (5-minute test every Monday at 10 AM)")

    if added_count > 0:
        _save_schedules(schedules)
        print(f"\n📅 {added_count} scheduled task(s) added")
        print()
        print("💡 To view all schedules:")
        print("   power-benchmark schedule list")
        print()
        print("💡 To run a schedule now:")
        print("   power-benchmark schedule run --id <ID>")
        print()
        print("⚠️  Note: These schedules are stored in your config.")
        print("   For system-level automation (cron/launchd), you'll need to set that up separately.")
        print()
    else:
        print("\n❌ No schedules added. Use --health-check, --power-monitor, or --all")
        print()

    return 0

