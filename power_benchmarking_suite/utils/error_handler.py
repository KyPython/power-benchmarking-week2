"""
Error Handler Utilities

Provides functions for handling errors with actionable guidance.
"""

import os
import sys
import subprocess
import logging
from typing import Optional, Tuple
from ..errors import (
    PowerBenchmarkError,
    PowerMetricsPermissionError,
    PowerMetricsNotFoundError,
    SystemCompatibilityError,
)

logger = logging.getLogger(__name__)


def check_sudo_permissions(command: str = "powermetrics") -> Tuple[bool, Optional[str]]:
    """
    Check if command can be run with sudo.

    Args:
        command: Command to check (default: powermetrics)

    Returns:
        Tuple of (has_permission, error_message)
    """
    # Check if we're already root
    if os.geteuid() == 0:
        return True, None

    # Check if command exists
    try:
        result = subprocess.run(["which", command], capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            return False, f"Command '{command}' not found in PATH"
    except Exception as e:
        logger.warning(f"Error checking for {command}: {e}")
        return False, f"Could not verify {command} availability"

    # Check if sudo is available
    try:
        result = subprocess.run(["which", "sudo"], capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            return False, "sudo command not found. This tool requires sudo for power monitoring."
    except Exception:
        return False, "Could not verify sudo availability"

    return True, None


def handle_permission_error(command: str, error: Exception) -> PowerMetricsPermissionError:
    """
    Convert a permission error into an actionable PowerMetricsPermissionError.

    Args:
        command: Command that failed
        error: Original exception

    Returns:
        PowerMetricsPermissionError with actionable guidance
    """
    return PowerMetricsPermissionError(command=command)


def check_powermetrics_availability() -> Tuple[bool, Optional[PowerBenchmarkError]]:
    """
    Check if powermetrics is available and accessible.

    Returns:
        Tuple of (is_available, error_if_not)
    """
    # Check if powermetrics exists
    try:
        result = subprocess.run(
            ["which", "powermetrics"], capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return False, PowerMetricsNotFoundError(
                "powermetrics command not found",
                actionable_help="""
🔧 How to Fix:

powermetrics is a macOS system tool that should be available by default.

If it's missing:
1. Check macOS version (requires macOS 10.15+)
2. Try: /usr/bin/powermetrics --help
3. If still missing, you may need to reinstall macOS developer tools

💡 Alternative:
  Use test mode without powermetrics (limited functionality):
  power-benchmark monitor --test 30 --no-powermetrics
""",
            )
    except Exception as e:
        logger.warning(f"Error checking powermetrics: {e}")
        return False, PowerMetricsNotFoundError(f"Could not verify powermetrics availability: {e}")

    # Check permissions
    has_permission, error_msg = check_sudo_permissions("powermetrics")
    if not has_permission:
        return False, handle_permission_error("powermetrics", Exception(error_msg))

    return True, None


def format_error_for_user(error: Exception, verbose: bool = False) -> str:
    """
    Format an error for user-friendly display with empowering guidance.

    Args:
        error: Exception to format
        verbose: Show additional debugging information

    Returns:
        Formatted error message with actionable next steps
    """
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel

    try:
        console = Console()
        use_rich = True
    except:
        use_rich = False

    if isinstance(error, PowerMetricsPermissionError):
        # The Permission Gatekeeper: Empowering, not discouraging
        message = Text()
        message.append("🔐 Permission Check\n\n", style="bold yellow")
        message.append("powermetrics needs sudo to access hardware power sensors.\n", style="dim")
        message.append(
            "This is normal and safe - you'll be prompted for your password.\n\n", style="green"
        )
        message.append("✅ Quick Fix (Copy & Paste):\n\n", style="bold green")
        message.append("  sudo power-benchmark monitor --test 30\n\n", style="cyan")
        message.append("💡 What happens next:\n", style="bold")
        message.append("  1. You'll enter your password (one time)\n", style="dim")
        message.append("  2. Power monitoring starts immediately\n", style="dim")
        message.append("  3. You'll see real-time power data in 30 seconds\n\n", style="dim")
        message.append("🎯 Success Preview:\n", style="bold")
        message.append("  ⚡ Real-Time Power Monitoring\n", style="dim")
        message.append("  📊 ANE Power: 1234.5 mW\n", style="dim")
        message.append("  🔄 Inference: 2,040 inf/sec\n\n", style="dim")
        message.append("Ready to try? Just run the command above! 🚀\n\n", style="bold green")
        message.append("📚 Advanced Options:\n", style="bold")
        message.append("  • Passwordless sudo: See docs/INSTALLATION.md\n", style="dim")
        message.append(
            "  • Test mode (limited): power-benchmark monitor --test 30 --no-sudo\n", style="dim"
        )

        if use_rich:
            return Panel(message, title="🔧 Permission Required", border_style="yellow")
        else:
            return str(message)

    elif isinstance(error, PowerBenchmarkError):
        if use_rich:
            return Panel(str(error), title="⚠️ Error", border_style="red")
        else:
            return str(error)

    # For other exceptions, provide generic guidance
    error_type = type(error).__name__
    error_msg = str(error)

    guidance = f"""
❌ Error: {error_type}

{error_msg}

💡 Need Help?
  - Run: power-benchmark validate (check system compatibility)
  - Run: power-benchmark quickstart (interactive setup)
  - See: docs/README.md (troubleshooting guide)
  - Report: https://github.com/KyPython/power-benchmarking-week2/issues
"""

    if verbose:
        import traceback

        guidance += f"\n🔍 Debug Info:\n{traceback.format_exc()}"

    if use_rich:
        return Panel(guidance, title="❌ Error", border_style="red")
    else:
        return guidance
