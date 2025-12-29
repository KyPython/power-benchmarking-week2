#!/usr/bin/env python3
"""
Custom Exception Hierarchy for Power Benchmarking Suite

Provides structured error handling with clear error messages.
"""


class PowerBenchmarkError(Exception):
    """Base exception for all power benchmarking errors."""

    def __init__(self, message: str, actionable_help: str = None):
        """
        Initialize error with actionable help.

        Args:
            message: Error message
            actionable_help: Optional actionable guidance for fixing the error
        """
        super().__init__(message)
        self.message = message
        self.actionable_help = actionable_help

    def __str__(self) -> str:
        """Return formatted error message with actionable help."""
        if self.actionable_help:
            return f"{self.message}\n\n{self.actionable_help}"
        return self.message


class ConfigError(PowerBenchmarkError):
    """Configuration-related errors."""

    pass


class ConfigLoadError(ConfigError):
    """Failed to load configuration file."""

    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""

    pass


class PowerMetricsError(PowerBenchmarkError):
    """powermetrics-related errors."""

    pass


class PowerMetricsPermissionError(PowerMetricsError):
    """Insufficient permissions for powermetrics (requires sudo)."""

    def __init__(self, command: str = "powermetrics", message: str = None):
        """
        Initialize permission error with actionable guidance.

        Args:
            command: The command that requires sudo
            message: Optional custom message
        """
        if message is None:
            message = self._generate_actionable_message(command)
        super().__init__(message)
        self.command = command

    def _generate_actionable_message(self, command: str) -> str:
        """Generate actionable error message with fix instructions."""
        return f"""
❌ Permission Denied: {command} requires sudo privileges

🔧 How to Fix:

Option 1: Run with sudo (Recommended)
  sudo power-benchmark monitor --test 30

Option 2: Configure passwordless sudo (Advanced)
  1. Edit sudoers: sudo visudo
  2. Add line: your_username ALL=(ALL) NOPASSWD: /usr/bin/powermetrics
  3. Save and test

Option 3: Use test mode without sudo (Limited)
  power-benchmark monitor --test 30 --no-sudo
  (Note: Limited functionality, may not capture all power metrics)

💡 Why sudo is needed:
  powermetrics requires root access to read hardware power sensors.
  This is a macOS security requirement, not a limitation of this tool.

📚 More help: See docs/INSTALLATION.md for detailed setup instructions
"""


class PowerMetricsNotFoundError(PowerMetricsError):
    """powermetrics command not found."""

    pass


class ModelError(PowerBenchmarkError):
    """Model-related errors."""

    pass


class ModelNotFoundError(ModelError):
    """ML model file not found."""

    pass


class ModelLoadError(ModelError):
    """Failed to load ML model."""

    pass


class ArduinoError(PowerBenchmarkError):
    """Arduino-related errors."""

    pass


class ArduinoNotFoundError(ArduinoError):
    """Arduino device not found."""

    pass


class ArduinoConnectionError(ArduinoError):
    """Failed to connect to Arduino."""

    pass


class AnalysisError(PowerBenchmarkError):
    """Analysis-related errors."""

    pass


class DataFileError(AnalysisError):
    """Data file errors (CSV, etc.)."""

    pass


class DataFileNotFoundError(DataFileError):
    """Data file not found."""

    pass


class DataFileFormatError(DataFileError):
    """Data file format invalid."""

    pass


class ValidationError(PowerBenchmarkError):
    """Validation-related errors."""

    pass


class SystemCompatibilityError(ValidationError):
    """System compatibility check failed."""

    pass


class PremiumFeatureError(PowerBenchmarkError):
    """Premium feature access errors."""

    pass


class PremiumRequiredError(PremiumFeatureError):
    """Premium subscription required for this feature."""

    pass
