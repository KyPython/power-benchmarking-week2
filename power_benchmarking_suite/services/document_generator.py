"""
Document Generator

Provides document generation utilities (HTML, text, etc.).
Can be extended for specific document types.
"""

import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Document generation service."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize document generator.

        Args:
            output_dir: Output directory for documents (defaults to ~/.power_benchmarking/documents)
        """
        if output_dir is None:
            output_dir = Path.home() / ".power_benchmarking" / "documents"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        title: str,
        content: str,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate HTML report.

        Args:
            title: Report title
            content: HTML content
            output_path: Output file path (defaults to auto-generated)

        Returns:
            Path to generated HTML file or None if failed
        """
        if output_path is None:
            from datetime import datetime

            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
            filename = f"{safe_title.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.html"
            output_path = self.output_dir / filename

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2563eb;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {content}
</body>
</html>"""

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)

            logger.info(f"HTML document generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating HTML document: {e}", exc_info=True)
            return None

