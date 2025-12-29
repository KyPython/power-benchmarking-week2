"""
Monthly Check-in Management

Provides automated monthly check-in tracking and reminders.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..services.storage import StorageService
from .clients import ClientManager, ClientStatus

logger = logging.getLogger(__name__)


class CheckinManager:
    """Monthly check-in management service."""

    def __init__(
        self,
        storage: Optional[StorageService] = None,
        client_manager: Optional[ClientManager] = None,
    ):
        """Initialize check-in manager."""
        self.storage = storage or StorageService()
        self.client_manager = client_manager or ClientManager(storage)
        self.collection = "checkins"

    def get_due_checkins(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get clients due for check-ins.

        Args:
            days_ahead: Number of days ahead to check (default: 7)

        Returns:
            List of clients due for check-ins
        """
        active_clients = self.client_manager.get_clients_by_status(ClientStatus.ACTIVE)
        due_clients = []

        today = datetime.utcnow().date()
        check_date = today + timedelta(days=days_ahead)

        for client in active_clients:
            last_checkin = self.get_last_checkin(client["id"])

            if last_checkin:
                last_date = datetime.fromisoformat(last_checkin["date"]).date()
                days_since = (today - last_date).days

                # Check if due (30 days since last check-in)
                if days_since >= 30:
                    due_clients.append(
                        {
                            "client": client,
                            "daysSinceLastCheckin": days_since,
                            "lastCheckin": last_checkin,
                        }
                    )
            else:
                # No check-in yet, check if started 30+ days ago
                start_date = datetime.fromisoformat(client.get("startDate", "")).date()
                days_since_start = (today - start_date).days

                if days_since_start >= 30:
                    due_clients.append(
                        {
                            "client": client,
                            "daysSinceLastCheckin": days_since_start,
                            "lastCheckin": None,
                        }
                    )

        return due_clients

    def create_checkin(
        self,
        client_id: str,
        notes: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a check-in record.

        Args:
            client_id: Client ID
            notes: Check-in notes
            date: Check-in date (ISO format, defaults to today)

        Returns:
            Created check-in data
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()

        checkin = {
            "clientId": client_id,
            "date": date,
            "notes": notes or "",
            "createdAt": datetime.utcnow().isoformat(),
        }

        return self.storage.create(self.collection, checkin)

    def get_last_checkin(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent check-in for a client."""
        checkins = self.storage.get_all(
            self.collection, filter_func=lambda c: c.get("clientId") == client_id
        )

        if not checkins:
            return None

        # Sort by date (most recent first)
        checkins.sort(key=lambda c: c.get("date", ""), reverse=True)
        return checkins[0]

    def get_checkins_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all check-ins for a client."""
        checkins = self.storage.get_all(
            self.collection, filter_func=lambda c: c.get("clientId") == client_id
        )

        # Sort by date (most recent first)
        checkins.sort(key=lambda c: c.get("date", ""), reverse=True)
        return checkins

