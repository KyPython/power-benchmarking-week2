"""
Email Templates

Provides email template management and rendering.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)

try:
    from jinja2 import Environment, FileSystemLoader, Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("Jinja2 not available. Install with: pip install jinja2")


class EmailTemplate:
    """Represents an email template."""

    def __init__(self, name: str, subject: str, html: str):
        self.name = name
        self.subject = subject
        self.html = html
        self._template = None

        if JINJA2_AVAILABLE:
            self._template = Template(html)

    def render(self, context: Dict[str, Any]) -> str:
        """Render template with context."""
        if self._template:
            return self._template.render(**context)
        else:
            # Simple placeholder replacement if Jinja2 not available
            html = self.html
            for key, value in context.items():
                html = html.replace(f"{{{{{key}}}}}", str(value))
                html = html.replace(f"{{{{ {key} }}}}", str(value))
            return html

    def get_subject(self, context: Dict[str, Any]) -> str:
        """Get rendered subject."""
        if JINJA2_AVAILABLE:
            template = Template(self.subject)
            return template.render(**context)
        else:
            # Simple placeholder replacement
            subject = self.subject
            for key, value in context.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                subject = subject.replace(f"{{{{ {key} }}}}", str(value))
            return subject


class EmailTemplates:
    """Email template manager."""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize email templates.

        Args:
            templates_dir: Directory containing email templates (defaults to package templates)
        """
        if templates_dir is None:
            # Default to package templates directory
            package_dir = Path(__file__).parent.parent.parent
            templates_dir = package_dir / "templates" / "emails"

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self._templates: Dict[str, EmailTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load templates from directory or use defaults."""
        # Try to load from directory
        if JINJA2_AVAILABLE and self.templates_dir.exists():
            try:
                env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
                for template_file in self.templates_dir.glob("*.html"):
                    template_name = template_file.stem
                    try:
                        template = env.get_template(template_file.name)
                        # Extract subject from template metadata or filename
                        subject = f"Email from Power Benchmarking Suite"
                        self._templates[template_name] = EmailTemplate(
                            template_name, subject, template.source
                        )
                    except Exception as e:
                        logger.warning(f"Error loading template {template_file}: {e}")
            except Exception as e:
                logger.warning(f"Error loading templates from {self.templates_dir}: {e}")

        # Load default templates
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default email templates."""
        # Welcome email template
        welcome_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Power Benchmarking Suite</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Welcome to Power Benchmarking Suite!</h1>
                <p>Hi {{ contact_name }},</p>
                <p>Thank you for your interest in the Power Benchmarking Suite. We're excited to help you optimize power consumption on Apple Silicon.</p>
                <p>Here's what you can do next:</p>
                <ul>
                    <li>Run your first benchmark: <code>power-benchmark monitor --test 30</code></li>
                    <li>Analyze application power: <code>power-benchmark analyze app Safari</code></li>
                    <li>View documentation: See our README.md</li>
                </ul>
                <p>If you have any questions, feel free to reach out!</p>
                <p>Best regards,<br>The Power Benchmarking Team</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    <a href="{{ unsubscribe_url }}">Unsubscribe</a> | 
                    <a href="{{ preferences_url }}">Email Preferences</a>
                </p>
            </div>
        </body>
        </html>
        """

        self._templates["welcome"] = EmailTemplate(
            "welcome", "Welcome to Power Benchmarking Suite", welcome_html
        )

        # Check-in email template
        checkin_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Monthly Check-in</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2563eb;">Monthly Check-in</h1>
                <p>Hi {{ contact_name }},</p>
                <p>It's time for your monthly check-in! How are things going with the Power Benchmarking Suite?</p>
                <p>We'd love to hear about:</p>
                <ul>
                    <li>Any challenges you're facing</li>
                    <li>Features you'd like to see</li>
                    <li>Success stories from your team</li>
                </ul>
                <p>Feel free to reply to this email or schedule a call.</p>
                <p>Best regards,<br>The Power Benchmarking Team</p>
                <hr>
                <p style="font-size: 12px; color: #666;">
                    <a href="{{ unsubscribe_url }}">Unsubscribe</a> | 
                    <a href="{{ preferences_url }}">Email Preferences</a>
                </p>
            </div>
        </body>
        </html>
        """

        self._templates["checkin"] = EmailTemplate(
            "checkin", "Monthly Check-in - Power Benchmarking Suite", checkin_html
        )

    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get a template by name."""
        return self._templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self._templates.keys())
