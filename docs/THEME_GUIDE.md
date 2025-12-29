# Blue Theme Guide

## Overview

The Power Benchmarking Suite uses a consistent blue theme throughout the application for brand consistency.

## Color Palette

- **Primary**: `[bold blue]` - Main brand color for success messages, headers, and primary actions
- **Secondary**: `[blue]` - Info messages, secondary text, and highlights
- **Dim**: `[dim blue]` - Low power levels, subtle information
- **Warning**: `[yellow]` - Warnings (kept for visibility)
- **Error**: `[bold red]` - Errors (kept for visibility)

## Usage

### Rich Console Output

```python
from power_benchmarking_suite.theme import RICH_STYLES

# Primary (success messages)
console.print(f"{RICH_STYLES['primary']}✅ Success message[/]")

# Info
console.print(f"{RICH_STYLES['info']}ℹ️  Info message[/]")

# Or use direct strings
console.print("[bold blue]✅ Success[/bold blue]")
console.print("[blue]ℹ️  Info[/blue]")
```

### Table Styling

```python
table = Table(show_header=True, header_style="bold blue")
table.add_column("Metric", style="blue")
table.add_column("Value", style="bold blue")
```

### Panel Styling

```python
panel = Panel(
    content,
    title="[bold blue]Title[/bold blue]",
    border_style="blue"
)
```

## Files Updated

- ✅ `scripts/unified_benchmark.py` - All colors updated to blue theme
- ✅ `power_benchmarking_suite/theme.py` - Centralized theme configuration
- ✅ Power bars use blue gradient (dim blue → blue → bold blue)
- ✅ Tables use blue headers and columns
- ✅ Panels use blue borders and titles

## Consistency Rules

1. **Success messages**: Use `[bold blue]`
2. **Info messages**: Use `[blue]`
3. **Headers/Titles**: Use `[bold blue]`
4. **Tables**: Header style `bold blue`, columns `blue`
5. **Panels**: Border style `blue`, title `[bold blue]`
6. **Power levels**: Blue gradient (dim → blue → bold blue)


