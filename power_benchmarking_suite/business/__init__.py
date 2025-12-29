"""
Business Automation Module

Provides client management, invoice generation, check-ins, and workflow automation.
"""

from .clients import ClientManager, ClientStatus
from .invoices import InvoiceManager
from .checkins import CheckinManager
from .onboarding import OnboardingManager
from .workflows import WorkflowManager

__all__ = [
    "ClientManager",
    "ClientStatus",
    "InvoiceManager",
    "CheckinManager",
    "OnboardingManager",
    "WorkflowManager",
]

