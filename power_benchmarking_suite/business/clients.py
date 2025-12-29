"""
Client Management

Provides CRUD operations for client management.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..services.storage import StorageService

logger = logging.getLogger(__name__)


class ClientStatus:
    """Client status constants."""

    PROSPECT = "prospect"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"


class ClientManager:
    """Client management service."""

    def __init__(self, storage: Optional[StorageService] = None):
        """
        Initialize client manager.

        Args:
            storage: Storage service instance (creates default if not provided)
        """
        self.storage = storage or StorageService()
        self.collection = "clients"

    def create_client(
        self,
        company: str,
        contact_name: str,
        contact_email: str,
        contact_phone: Optional[str] = None,
        monthly_fee: float = 297.0,
        start_date: Optional[str] = None,
        status: str = ClientStatus.ONBOARDING,
        team_size: Optional[int] = None,
        tech_stack: Optional[List[str]] = None,
        repository: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new client.

        Args:
            company: Company name
            contact_name: Contact person name
            contact_email: Contact email
            contact_phone: Contact phone (optional)
            monthly_fee: Monthly fee amount
            start_date: Start date (ISO format, defaults to today)
            status: Client status (default: onboarding)
            team_size: Team size (optional)
            tech_stack: Technology stack (optional)
            repository: Repository URL (optional)

        Returns:
            Created client data
        """
        if start_date is None:
            start_date = datetime.utcnow().date().isoformat()

        client = {
            "company": company,
            "contact": {
                "name": contact_name,
                "email": contact_email,
                "phone": contact_phone,
            },
            "startDate": start_date,
            "status": status,
            "monthlyFee": monthly_fee,
            "teamSize": team_size,
            "techStack": tech_stack or [],
            "repository": repository,
        }

        return self.storage.create(self.collection, client)

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client by ID."""
        return self.storage.get(self.collection, client_id)

    def get_client_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get client by email."""
        clients = self.storage.get_all(
            self.collection, filter_func=lambda c: c.get("contact", {}).get("email") == email
        )
        return clients[0] if clients else None

    def get_clients_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get clients by status."""
        return self.storage.get_all(
            self.collection, filter_func=lambda c: c.get("status") == status
        )

    def list_clients(self) -> List[Dict[str, Any]]:
        """List all clients."""
        return self.storage.get_all(self.collection)

    def update_client(self, client_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update client.

        Args:
            client_id: Client ID
            updates: Dictionary of fields to update

        Returns:
            Updated client data or None if not found
        """
        return self.storage.update(self.collection, client_id, updates)

    def update_client_status(self, client_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update client status."""
        return self.update_client(client_id, {"status": status})

    def delete_client(self, client_id: str) -> bool:
        """Delete client."""
        return self.storage.delete(self.collection, client_id)

