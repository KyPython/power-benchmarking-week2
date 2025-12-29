"""
Onboarding Management

Provides onboarding progress tracking and reminders.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..services.storage import StorageService
from .clients import ClientManager, ClientStatus

logger = logging.getLogger(__name__)


class OnboardingManager:
    """Onboarding management service."""

    def __init__(
        self,
        storage: Optional[StorageService] = None,
        client_manager: Optional[ClientManager] = None,
    ):
        """Initialize onboarding manager."""
        self.storage = storage or StorageService()
        self.client_manager = client_manager or ClientManager(storage)
        self.collection = "onboarding"

    def get_checklist(self, client_id: str) -> Dict[str, Any]:
        """
        Get onboarding checklist for a client.

        Args:
            client_id: Client ID

        Returns:
            Checklist with progress
        """
        onboarding = self.storage.get(self.collection, client_id)

        if not onboarding:
            # Create default checklist
            onboarding = self._create_default_checklist(client_id)

        return onboarding

    def _create_default_checklist(self, client_id: str) -> Dict[str, Any]:
        """Create default onboarding checklist."""
        checklist = {
            "id": client_id,  # Use client_id as onboarding ID
            "clientId": client_id,
            "steps": [
                {"id": "welcome_email", "name": "Welcome Email Sent", "completed": False},
                {"id": "initial_setup", "name": "Initial Setup Complete", "completed": False},
                {"id": "first_benchmark", "name": "First Benchmark Run", "completed": False},
                {
                    "id": "documentation_review",
                    "name": "Documentation Reviewed",
                    "completed": False,
                },
                {"id": "integration_complete", "name": "Integration Complete", "completed": False},
            ],
            "progress": 0,
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }

        return self.storage.create(self.collection, checklist)

    def update_progress(
        self, client_id: str, step_id: str, completed: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Update onboarding progress.

        Args:
            client_id: Client ID
            step_id: Step ID to update
            completed: Whether step is completed

        Returns:
            Updated checklist
        """
        checklist = self.get_checklist(client_id)

        # Update step
        for step in checklist.get("steps", []):
            if step.get("id") == step_id:
                step["completed"] = completed
                break

        # Calculate progress
        total_steps = len(checklist.get("steps", []))
        completed_steps = sum(1 for s in checklist.get("steps", []) if s.get("completed"))
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        # Update client status if complete
        if progress >= 100:
            self.client_manager.update_client_status(client_id, ClientStatus.ACTIVE)

        return self.storage.update(
            self.collection,
            client_id,
            {
                "steps": checklist["steps"],
                "progress": progress,
                "updatedAt": datetime.utcnow().isoformat(),
            },
        )

    def get_reminders(self, days_inactive: int = 7) -> List[Dict[str, Any]]:
        """
        Get clients needing onboarding reminders.

        Args:
            days_inactive: Days since last activity (default: 7)

        Returns:
            List of clients needing reminders
        """
        onboarding_clients = self.client_manager.get_clients_by_status(ClientStatus.ONBOARDING)
        reminders = []

        today = datetime.utcnow()

        for client in onboarding_clients:
            checklist = self.get_checklist(client["id"])
            last_update = datetime.fromisoformat(
                checklist.get("updatedAt", checklist.get("createdAt"))
            )
            days_since = (today - last_update).days

            if days_since >= days_inactive and checklist.get("progress", 0) < 100:
                reminders.append(
                    {
                        "client": client,
                        "checklist": checklist,
                        "daysSinceLastActivity": days_since,
                    }
                )

        return reminders

