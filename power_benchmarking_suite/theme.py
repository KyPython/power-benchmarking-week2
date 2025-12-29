"""
Theme Configuration for Power Benchmarking Suite

Centralized blue theme configuration for consistent branding.
"""

# Blue theme colors
THEME = {
    "primary": "blue",
    "secondary": "cyan",
    "success": "blue",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "dim": "dim",
    "bold": "bold",
}

# Rich style mappings
RICH_STYLES = {
    "primary": "[bold blue]",
    "secondary": "[cyan]",
    "success": "[bold blue]",
    "warning": "[yellow]",
    "error": "[bold red]",
    "info": "[blue]",
    "dim": "[dim]",
    "title": "[bold blue]",
    "header": "[bold blue]",
    "highlight": "[bold cyan]",
    "border": "blue",
}


# Console color functions
def get_style(style_name: str) -> str:
    """Get Rich style string for a style name."""
    return RICH_STYLES.get(style_name, "[blue]")


def primary(text: str) -> str:
    """Format text with primary (blue) color."""
    return f"{RICH_STYLES['primary']}{text}[/]"


def success(text: str) -> str:
    """Format text with success (blue) color."""
    return f"{RICH_STYLES['success']}{text}[/]"


def info(text: str) -> str:
    """Format text with info (blue) color."""
    return f"{RICH_STYLES['info']}{text}[/]"


def warning(text: str) -> str:
    """Format text with warning (yellow) color."""
    return f"{RICH_STYLES['warning']}{text}[/]"


def error(text: str) -> str:
    """Format text with error (red) color."""
    return f"{RICH_STYLES['error']}{text}[/]"


def highlight(text: str) -> str:
    """Format text with highlight (cyan) color."""
    return f"{RICH_STYLES['highlight']}{text}[/]"


def dim(text: str) -> str:
    """Format text with dim style."""
    return f"{RICH_STYLES['dim']}{text}[/]"

