"""
Marketing Module

Provides lead capture, email automation, and presentation tools.
"""

from .lead_capture import LeadCapture
from .email_service import EmailService
from .email_templates import EmailTemplates

__all__ = [
    "LeadCapture",
    "EmailService",
    "EmailTemplates",
]

