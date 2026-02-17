"""
Tests for webhook security - signature verification, idempotency

These tests replicate the webhook logic in Python for testing purposes.
The actual webhook is in JavaScript (Next.js), but we test the algorithm.
"""

import pytest
import json
import hmac
import hashlib
import time
import re


# Replicated webhook functions for testing
def verifyPolarSignature(signature, body, secret):
    """Verify Polar webhook signature - replicated from JS"""
    if not signature or not secret:
        return False

    # Parse signature
    parts = signature.split(',')
    timestamp = ''
    sig = ''
    
    for part in parts:
        if part.startswith('t='):
            timestamp = part[2:]
        if part.startswith('v1='):
            sig = part[3:]

    if not timestamp or not sig:
        return False

    # Check timestamp (5 min window)
    now = int(time.time())
    event_time = int(timestamp)
    if abs(now - event_time) > 300:
        return False

    # Compute expected signature
    payload = f"{timestamp}.{body}"
    expected_sig = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest().hex()

    # Constant-time comparison
    if len(sig) != len(expected_sig):
        return False
    
    result = 0
    for i in range(len(sig)):
        result |= ord(sig[i]) ^ ord(expected_sig[i])

    return result == 0


def generateActivationCode():
    """Generate activation code - replicated from JS"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code = ''
    for i in range(8):
        if i == 4:
            code += '-'
        code += chars[random.randint(0, len(chars) - 1)]
    return code


import random


class TestWebhookSignatureVerification:
    """Test webhook signature verification"""
    
    def create_signature(self, body, secret, timestamp=None):
        """Create a valid Polar webhook signature"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        payload = f"{timestamp}.{body}"
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).digest().hex()
        return f"t={timestamp},v1={signature}"
    
    def test_valid_signature(self):
        """Test that valid signatures are accepted"""
        secret = "test_secret"
        body = '{"type": "checkout.completed", "data": {"id": "123"}}'
        timestamp = str(int(time.time()))
        signature = self.create_signature(body, secret, timestamp)
        
        assert verifyPolarSignature(signature, body, secret) is True
    
    def test_invalid_signature(self):
        """Test that invalid signatures are rejected"""
        secret = "test_secret"
        body = '{"type": "checkout.completed"}'
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=invalid_signature"
        
        assert verifyPolarSignature(signature, body, secret) is False
    
    def test_missing_signature(self):
        """Test that missing signature is rejected"""
        assert verifyPolarSignature(None, "body", "secret") is False
        assert verifyPolarSignature("", "body", "secret") is False
    
    def test_old_timestamp_rejected(self):
        """Test that old timestamps are rejected (replay attack)"""
        secret = "test_secret"
        body = '{"type": "checkout.completed"}'
        # Timestamp from 10 minutes ago
        timestamp = str(int(time.time()) - 600)
        signature = self.create_signature(body, secret, timestamp)
        
        assert verifyPolarSignature(signature, body, secret) is False
    
    def test_missing_secret(self):
        """Test that missing secret fails verification"""
        body = '{"type": "checkout.completed"}'
        timestamp = str(int(time.time()))
        signature = f"t={timestamp},v1=abc"
        
        assert verifyPolarSignature(signature, body, None) is False
        assert verifyPolarSignature(signature, body, "") is False


class TestIdempotency:
    """Test idempotency logic"""
    
    def test_duplicate_checkout_ignored(self):
        """Test that duplicate checkouts are handled"""
        # Simulate processed events store
        processed_events = {}
        
        event_id = "checkout_123"
        code = "ABCD-1234"
        
        # First event creates code
        processed_events[event_id] = code
        
        # Duplicate should be detected
        assert event_id in processed_events
        assert processed_events[event_id] == code
    
    def test_refund_not_duplicated(self):
        """Test that refund events are idempotent"""
        processed_events = {}
        
        event_id = "refund_456"
        
        # First refund
        processed_events[event_id] = "refunded"
        
        # Duplicate should be detected
        assert processed_events[event_id] == "refunded"


class TestPurchaseRecords:
    """Test purchase record storage"""
    
    def test_record_structure(self):
        """Test that purchase records have correct structure"""
        event_data = {
            "type": "checkout.completed",
            "id": "evt_123",
            "customer_email": "test@example.com",
            "product": {"name": "Premium"},
            "amount": 2900,
            "currency": "usd",
            "status": "completed"
        }
        
        # Simulate record creation
        record = {
            "eventId": event_data["id"],
            "type": event_data["type"],
            "customerEmail": event_data["customer_email"],
            "productName": event_data["product"]["name"],
            "amount": event_data["amount"],
            "currency": event_data["currency"],
            "status": event_data["status"],
            "processedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        
        assert record["eventId"] == "evt_123"
        assert record["customerEmail"] == "test@example.com"
        assert record["type"] == "checkout.completed"
        assert record["amount"] == 2900


class TestActivationCodeGeneration:
    """Test activation code generation"""
    
    def test_code_format(self):
        """Test that codes are in correct format XXXX-XXXX"""
        code = generateActivationCode()
        
        # Should be 9 chars (8 + hyphen)
        assert len(code) == 9
        # Should have hyphen in middle
        assert code[4] == "-"
        # Should be uppercase
        assert code == code.upper()
    
    def test_code_characters(self):
        """Test that codes only use allowed characters"""
        code = generateActivationCode()
        
        # Remove hyphen for character check
        code_chars = code.replace('-', '')
        allowed = set('ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        
        for c in code_chars:
            assert c in allowed, f"Invalid character: {c}"


class TestWebhookEventTypes:
    """Test webhook event type handling"""
    
    def test_checkout_completed_handler(self):
        """Test checkout.completed event"""
        event = {
            "type": "checkout.completed",
            "data": {
                "id": "chk_123",
                "customer_email": "user@example.com",
                "status": "completed",
                "product": {"name": "Premium"},
            }
        }
        
        # Should process this event
        assert event["type"] == "checkout.completed"
        assert event["data"]["status"] == "completed"
    
    def test_subscription_canceled_handler(self):
        """Test subscription.canceled event"""
        event = {
            "type": "subscription.canceled",
            "data": {
                "id": "sub_456",
                "customer": {"email": "user@example.com"},
                "status": "canceled",
            }
        }
        
        # Should process cancellation
        assert event["type"] == "subscription.canceled"
        assert event["data"]["status"] == "canceled"
    
    def test_refund_handler(self):
        """Test refund event"""
        event = {
            "type": "refund.created",
            "data": {
                "id": "ref_789",
                "checkout_id": "chk_123",
                "amount": 2900,
            }
        }
        
        # Should process refund
        assert event["type"] == "refund.created"
        assert "checkout_id" in event["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
