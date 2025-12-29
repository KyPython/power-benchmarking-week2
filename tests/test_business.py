#!/usr/bin/env python3
"""
Unit tests for business automation modules.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from power_benchmarking_suite.business import (
    ClientManager,
    ClientStatus,
    InvoiceManager,
    CheckinManager,
    OnboardingManager,
)
from power_benchmarking_suite.services import StorageService


class TestClientManager(unittest.TestCase):
    """Test client management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageService(storage_path=self.temp_dir)
        self.manager = ClientManager(storage=self.storage)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_client(self):
        """Test client creation."""
        client = self.manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

        self.assertIsNotNone(client)
        self.assertIn("id", client)
        self.assertEqual(client["company"], "Test Corp")
        self.assertEqual(client["contact"]["email"], "john@test.com")
        self.assertEqual(client["status"], ClientStatus.ONBOARDING)

    def test_get_client(self):
        """Test getting client by ID."""
        client = self.manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

        retrieved = self.manager.get_client(client["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], client["id"])

    def test_get_client_by_email(self):
        """Test getting client by email."""
        self.manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

        client = self.manager.get_client_by_email("john@test.com")
        self.assertIsNotNone(client)
        self.assertEqual(client["contact"]["email"], "john@test.com")

    def test_list_clients(self):
        """Test listing clients."""
        self.manager.create_client(
            company="Test Corp 1",
            contact_name="John Doe",
            contact_email="john@test.com",
        )
        self.manager.create_client(
            company="Test Corp 2",
            contact_name="Jane Smith",
            contact_email="jane@test.com",
        )

        clients = self.manager.list_clients()
        self.assertEqual(len(clients), 2)

    def test_update_client(self):
        """Test updating client."""
        client = self.manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

        updated = self.manager.update_client_status(client["id"], ClientStatus.ACTIVE)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], ClientStatus.ACTIVE)


class TestInvoiceManager(unittest.TestCase):
    """Test invoice management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageService(storage_path=self.temp_dir)
        self.client_manager = ClientManager(storage=self.storage)
        self.invoice_manager = InvoiceManager(storage=self.storage)

        # Create a test client
        self.client = self.client_manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_invoice(self):
        """Test invoice creation."""
        invoice = self.invoice_manager.create_invoice(
            client_id=self.client["id"],
            amount=199.00,
            description="Monthly subscription",
        )

        self.assertIsNotNone(invoice)
        self.assertIn("id", invoice)
        self.assertEqual(invoice["clientId"], self.client["id"])
        self.assertEqual(invoice["amount"], 199.00)
        self.assertEqual(invoice["status"], "pending")

    def test_get_invoices_by_client(self):
        """Test getting invoices for a client."""
        self.invoice_manager.create_invoice(
            client_id=self.client["id"],
            amount=199.00,
            description="Invoice 1",
        )
        self.invoice_manager.create_invoice(
            client_id=self.client["id"],
            amount=299.00,
            description="Invoice 2",
        )

        invoices = self.invoice_manager.get_invoices_by_client(self.client["id"])
        self.assertEqual(len(invoices), 2)

    def test_mark_paid(self):
        """Test marking invoice as paid."""
        invoice = self.invoice_manager.create_invoice(
            client_id=self.client["id"],
            amount=199.00,
            description="Test invoice",
        )

        paid = self.invoice_manager.mark_paid(invoice["id"])
        self.assertIsNotNone(paid)
        self.assertEqual(paid["status"], "paid")
        self.assertIn("paidAt", paid)


class TestCheckinManager(unittest.TestCase):
    """Test check-in management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageService(storage_path=self.temp_dir)
        self.client_manager = ClientManager(storage=self.storage)
        self.checkin_manager = CheckinManager(
            storage=self.storage, client_manager=self.client_manager
        )

        # Create a test client
        self.client = self.client_manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
            status=ClientStatus.ACTIVE,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_checkin(self):
        """Test check-in creation."""
        checkin = self.checkin_manager.create_checkin(
            client_id=self.client["id"],
            notes="Monthly check-in completed",
        )

        self.assertIsNotNone(checkin)
        self.assertIn("id", checkin)
        self.assertEqual(checkin["clientId"], self.client["id"])
        self.assertEqual(checkin["notes"], "Monthly check-in completed")

    def test_get_checkins_by_client(self):
        """Test getting check-ins for a client."""
        self.checkin_manager.create_checkin(
            client_id=self.client["id"],
            notes="Check-in 1",
        )
        self.checkin_manager.create_checkin(
            client_id=self.client["id"],
            notes="Check-in 2",
        )

        checkins = self.checkin_manager.get_checkins_by_client(self.client["id"])
        self.assertEqual(len(checkins), 2)


if __name__ == "__main__":
    unittest.main()

