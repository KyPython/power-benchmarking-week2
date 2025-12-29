"""
Lead Capture

Provides lead capture and automated email sequence triggering.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from ..business.clients import ClientManager, ClientStatus
from ..business.onboarding import OnboardingManager
from .email_service import EmailService
from .email_templates import EmailTemplates

logger = logging.getLogger(__name__)


class LeadCapture:
    """Lead capture service."""

    def __init__(
        self,
        client_manager: Optional[ClientManager] = None,
        onboarding_manager: Optional[OnboardingManager] = None,
        email_service: Optional[EmailService] = None,
    ):
        """Initialize lead capture."""
        self.client_manager = client_manager or ClientManager()
        self.onboarding_manager = onboarding_manager or OnboardingManager()
        self.email_service = email_service or EmailService()
        self.templates = EmailTemplates()

    def capture_lead(
        self,
        name: str,
        email: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        send_welcome_email: bool = True,
    ) -> Dict[str, Any]:
        """
        Capture a new lead and trigger onboarding.

        Args:
            name: Contact name
            email: Contact email
            company: Company name (optional)
            phone: Contact phone (optional)
            send_welcome_email: Whether to send welcome email (default: True)

        Returns:
            Result dict with client data and email status
        """
        logger.info(f"Capturing lead: {name} <{email}>")

        # Check if client already exists
        existing_client = self.client_manager.get_client_by_email(email)

        if existing_client:
            logger.info(f"Client already exists: {existing_client['id']}")
            return {
                "success": True,
                "client": existing_client,
                "is_new": False,
                "email_sent": False,
            }

        # Create new client
        client = self.client_manager.create_client(
            company=company or name,
            contact_name=name,
            contact_email=email,
            contact_phone=phone,
            status=ClientStatus.ONBOARDING,
        )

        # Initialize onboarding checklist
        self.onboarding_manager.get_checklist(client["id"])

        # Send welcome email
        email_sent = False
        if send_welcome_email:
            try:
                context = {
                    "contact_name": name,
                    "company": company or name,
                    "unsubscribe_url": f"#",  # TODO: Generate proper URL
                    "preferences_url": f"#",  # TODO: Generate proper URL
                }

                email_result = self.email_service.send_template_email(
                    to=email, template_name="welcome", context=context
                )

                email_sent = email_result.get("success", False)

                if email_sent:
                    # Mark welcome email step as complete
                    self.onboarding_manager.update_progress(
                        client["id"], "welcome_email", completed=True
                    )

            except Exception as e:
                logger.error(f"Error sending welcome email: {e}")

        logger.info(f"Lead captured successfully: {client['id']}")

        return {
            "success": True,
            "client": client,
            "is_new": True,
            "email_sent": email_sent,
        }

