"""
Email Service

Provides email sending capabilities using Resend API.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from resend import Resend

    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend library not available. Install with: pip install resend")


class EmailService:
    """Email service using Resend API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        """
        Initialize email service.

        Args:
            api_key: Resend API key (defaults to RESEND_API_KEY env var)
            from_email: From email address (defaults to FROM_EMAIL env var)
            from_name: From name (defaults to FROM_NAME env var)
        """
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@example.com")
        self.from_name = from_name or os.getenv("FROM_NAME", "Power Benchmarking Suite")

        if RESEND_AVAILABLE and self.api_key:
            self.resend = Resend(api_key=self.api_key)
        else:
            self.resend = None
            if not RESEND_AVAILABLE:
                logger.warning("Resend library not installed")
            if not self.api_key:
                logger.warning("RESEND_API_KEY not configured")

    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML email content
            from_email: From email (defaults to configured from_email)
            attachments: List of attachment dicts with 'filename' and 'content'

        Returns:
            Result dict with 'success' and optional 'message_id' or 'error'
        """
        if not self.resend:
            # In development mode or when API key is missing, simulate success
            if (
                os.getenv("NODE_ENV") == "development"
                or os.getenv("PYTHON_ENV") == "development"
                or not self.api_key
            ):
                logger.info(f"Email would be sent: to={to}, subject={subject}")
                return {"success": True, "message_id": "dev-mode"}
            return {"success": False, "error": "Email service not configured"}

        try:
            from_addr = from_email or self.from_email

            params = {
                "from": f"{self.from_name} <{from_addr}>",
                "to": [to],
                "subject": subject,
                "html": html,
            }

            if attachments:
                params["attachments"] = attachments

            result = self.resend.emails.send(**params)

            if result and hasattr(result, "id"):
                logger.info(f"Email sent successfully: {result.id}")
                return {"success": True, "message_id": result.id}
            else:
                logger.error(f"Email send failed: {result}")
                return {"success": False, "error": "Unknown error"}

        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def send_template_email(
        self,
        to: str,
        template_name: str,
        context: Dict[str, Any],
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using a template.

        Args:
            to: Recipient email address
            template_name: Template name (will be loaded from email_templates)
            context: Template context variables
            subject: Email subject (defaults to template subject)

        Returns:
            Result dict with 'success' and optional 'message_id' or 'error'
        """
        from .email_templates import EmailTemplates

        templates = EmailTemplates()
        template = templates.get_template(template_name)

        if not template:
            return {"success": False, "error": f"Template not found: {template_name}"}

        html = template.render(context)
        email_subject = subject or template.get_subject(context)

        return self.send_email(to=to, subject=email_subject, html=html)
