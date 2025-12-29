#!/usr/bin/env python3
"""
Unit tests for marketing automation modules.
"""

import unittest
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock

from power_benchmarking_suite.marketing import (
    LeadCapture,
    EmailService,
    EmailTemplates,
)
from power_benchmarking_suite.business import ClientManager
from power_benchmarking_suite.services import StorageService


class TestEmailTemplates(unittest.TestCase):
    """Test email templates."""

    def test_list_templates(self):
        """Test listing templates."""
        templates = EmailTemplates()
        template_names = templates.list_templates()

        self.assertGreater(len(template_names), 0)
        self.assertIn("welcome", template_names)
        self.assertIn("checkin", template_names)

    def test_get_template(self):
        """Test getting a template."""
        templates = EmailTemplates()
        template = templates.get_template("welcome")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "welcome")

    def test_render_template(self):
        """Test rendering a template."""
        templates = EmailTemplates()
        template = templates.get_template("welcome")

        context = {
            "contact_name": "John Doe",
            "company": "Test Corp",
            "unsubscribe_url": "#",
            "preferences_url": "#",
        }

        html = template.render(context)
        self.assertIn("John Doe", html)
        # Note: 'company' is not used in welcome template, only contact_name
        # So we just verify the template renders successfully
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 100)  # Template should have content

    def test_get_subject(self):
        """Test getting template subject."""
        templates = EmailTemplates()
        template = templates.get_template("welcome")

        context = {"contact_name": "John"}
        subject = template.get_subject(context)
        self.assertIsInstance(subject, str)
        self.assertGreater(len(subject), 0)


class TestEmailService(unittest.TestCase):
    """Test email service."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(
            os.environ,
            {
                "RESEND_API_KEY": "test_key",
                "FROM_EMAIL": "test@example.com",
                "FROM_NAME": "Test Suite",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

    def test_email_service_init(self):
        """Test email service initialization."""
        service = EmailService()
        self.assertIsNotNone(service)
        self.assertEqual(service.from_email, "test@example.com")
        self.assertEqual(service.from_name, "Test Suite")

    @patch("power_benchmarking_suite.marketing.email_service.RESEND_AVAILABLE", False)
    def test_send_email_dev_mode(self):
        """Test sending email in dev mode (no Resend)."""
        # Set environment to development mode
        with patch.dict(os.environ, {"PYTHON_ENV": "development"}, clear=False):
            service = EmailService()
            result = service.send_email(to="test@example.com", subject="Test", html="<p>Test</p>")

            # Should succeed in dev mode
            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("message_id"), "dev-mode")


class TestLeadCapture(unittest.TestCase):
    """Test lead capture."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = StorageService(storage_path=self.temp_dir)
        self.client_manager = ClientManager(storage=self.storage)
        self.lead_capture = LeadCapture(
            client_manager=self.client_manager,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_capture_lead(self):
        """Test capturing a lead."""
        result = self.lead_capture.capture_lead(
            name="John Doe",
            email="john@test.com",
            company="Test Corp",
            send_welcome_email=False,  # Skip email for test
        )

        self.assertTrue(result.get("success"))
        self.assertTrue(result.get("is_new"))
        self.assertIsNotNone(result.get("client"))
        self.assertIn("id", result["client"])

    def test_capture_existing_lead(self):
        """Test capturing an existing lead."""
        # Create client first
        self.client_manager.create_client(
            company="Test Corp",
            contact_name="John Doe",
            contact_email="john@test.com",
        )

        # Try to capture again
        result = self.lead_capture.capture_lead(
            name="John Doe",
            email="john@test.com",
            company="Test Corp",
            send_welcome_email=False,
        )

        self.assertTrue(result.get("success"))
        self.assertFalse(result.get("is_new"))  # Should be existing


if __name__ == "__main__":
    unittest.main()
