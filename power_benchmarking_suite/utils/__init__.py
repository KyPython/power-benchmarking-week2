"""
Utility modules for power benchmarking suite.
"""

from .error_handler import (
    check_sudo_permissions,
    handle_permission_error,
    check_powermetrics_availability,
    format_error_for_user,
)

__all__ = [
    "check_sudo_permissions",
    "handle_permission_error",
    "check_powermetrics_availability",
    "format_error_for_user",
]

