"""
Workflow Automation

Provides automated workflow execution and scheduling.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from .clients import ClientManager
from .checkins import CheckinManager
from .onboarding import OnboardingManager
from ..marketing.email_service import EmailService
from ..marketing.email_templates import EmailTemplates

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Workflow automation manager."""

    def __init__(
        self,
        client_manager: Optional[ClientManager] = None,
        checkin_manager: Optional[CheckinManager] = None,
        onboarding_manager: Optional[OnboardingManager] = None,
        email_service: Optional[EmailService] = None,
    ):
        """Initialize workflow manager."""
        self.client_manager = client_manager or ClientManager()
        self.checkin_manager = checkin_manager or CheckinManager()
        self.onboarding_manager = onboarding_manager or OnboardingManager()
        self.email_service = email_service or EmailService()
        self.templates = EmailTemplates()

    def run_checkins(self, send_emails: bool = True) -> Dict[str, Any]:
        """
        Run check-in workflow - find due clients and optionally send emails.

        Args:
            send_emails: Whether to send check-in emails (default: True)

        Returns:
            Workflow execution results
        """
        logger.info("Running check-in workflow...")

        due_checkins = self.checkin_manager.get_due_checkins()
        results = {
            "total_due": len(due_checkins),
            "emails_sent": 0,
            "errors": [],
        }

        for item in due_checkins:
            client = item["client"]
            client_id = client["id"]
            contact_email = client.get("contact", {}).get("email")

            try:
                # Create check-in record
                checkin = self.checkin_manager.create_checkin(
                    client_id=client_id, notes=f"Automated check-in reminder"
                )

                # Send email if requested
                if send_emails and contact_email:
                    context = {
                        "contact_name": client.get("contact", {}).get("name", "there"),
                        "company": client.get("company", ""),
                        "unsubscribe_url": f"#",  # TODO: Generate proper URL
                        "preferences_url": f"#",  # TODO: Generate proper URL
                    }

                    email_result = self.email_service.send_template_email(
                        to=contact_email, template_name="checkin", context=context
                    )

                    if email_result.get("success"):
                        results["emails_sent"] += 1
                    else:
                        results["errors"].append(
                            {
                                "client_id": client_id,
                                "error": email_result.get("error", "Unknown error"),
                            }
                        )

            except Exception as e:
                logger.error(f"Error processing check-in for client {client_id}: {e}")
                results["errors"].append({"client_id": client_id, "error": str(e)})

        logger.info(f"Check-in workflow complete: {results['emails_sent']} emails sent")
        return results

    def run_reminders(self, send_emails: bool = True) -> Dict[str, Any]:
        """
        Run onboarding reminder workflow.

        Args:
            send_emails: Whether to send reminder emails (default: True)

        Returns:
            Workflow execution results
        """
        logger.info("Running onboarding reminder workflow...")

        reminders = self.onboarding_manager.get_reminders()
        results = {
            "total_reminders": len(reminders),
            "emails_sent": 0,
            "errors": [],
        }

        for item in reminders:
            client = item["client"]
            client_id = client["id"]
            contact_email = client.get("contact", {}).get("email")

            try:
                if send_emails and contact_email:
                    context = {
                        "contact_name": client.get("contact", {}).get("name", "there"),
                        "company": client.get("company", ""),
                        "progress": item["checklist"].get("progress", 0),
                        "unsubscribe_url": f"#",  # TODO: Generate proper URL
                        "preferences_url": f"#",  # TODO: Generate proper URL
                    }

                    email_result = self.email_service.send_template_email(
                        to=contact_email,
                        template_name="welcome",  # Could create a reminder template
                        context=context,
                    )

                    if email_result.get("success"):
                        results["emails_sent"] += 1
                    else:
                        results["errors"].append(
                            {
                                "client_id": client_id,
                                "error": email_result.get("error", "Unknown error"),
                            }
                        )

            except Exception as e:
                logger.error(f"Error processing reminder for client {client_id}: {e}")
                results["errors"].append({"client_id": client_id, "error": str(e)})

        logger.info(f"Reminder workflow complete: {results['emails_sent']} emails sent")
        return results

