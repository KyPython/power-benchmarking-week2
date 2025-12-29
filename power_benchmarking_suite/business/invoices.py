"""
Invoice Management

Provides invoice generation and management.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..services.storage import StorageService

logger = logging.getLogger(__name__)


class InvoiceManager:
    """Invoice management service."""

    def __init__(self, storage: Optional[StorageService] = None):
        """Initialize invoice manager."""
        self.storage = storage or StorageService()
        self.collection = "invoices"

    def create_invoice(
        self,
        client_id: str,
        amount: float,
        description: str,
        due_date: Optional[str] = None,
        status: str = "pending",
    ) -> Dict[str, Any]:
        """
        Create a new invoice.

        Args:
            client_id: Client ID
            amount: Invoice amount
            description: Invoice description
            due_date: Due date (ISO format, defaults to 30 days from now)
            status: Invoice status (default: pending)

        Returns:
            Created invoice data
        """
        if due_date is None:
            from datetime import timedelta

            due_date = (datetime.utcnow() + timedelta(days=30)).date().isoformat()

        invoice = {
            "clientId": client_id,
            "amount": amount,
            "description": description,
            "dueDate": due_date,
            "status": status,
            "createdAt": datetime.utcnow().isoformat(),
        }

        return self.storage.create(self.collection, invoice)

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID."""
        return self.storage.get(self.collection, invoice_id)

    def get_invoices_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all invoices for a client."""
        return self.storage.get_all(
            self.collection, filter_func=lambda i: i.get("clientId") == client_id
        )

    def get_invoices_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get invoices by status."""
        return self.storage.get_all(
            self.collection, filter_func=lambda i: i.get("status") == status
        )

    def list_invoices(self) -> List[Dict[str, Any]]:
        """List all invoices."""
        return self.storage.get_all(self.collection)

    def update_invoice(self, invoice_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update invoice."""
        return self.storage.update(self.collection, invoice_id, updates)

    def mark_paid(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Mark invoice as paid."""
        return self.update_invoice(
            invoice_id, {"status": "paid", "paidAt": datetime.utcnow().isoformat()}
        )

    def delete_invoice(self, invoice_id: str) -> bool:
        """Delete invoice."""
        return self.storage.delete(self.collection, invoice_id)

