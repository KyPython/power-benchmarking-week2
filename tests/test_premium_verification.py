"""
Tests for premium feature verification
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestPremiumVerification:
    """Test premium entitlement verification"""
    
    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a temporary config file"""
        config_dir = tmp_path / ".power_benchmarking"
        config_dir.mkdir()
        config_file = config_dir / "premium_config.json"
        return config_file
    
    @patch('power_benchmarking_suite.premium.requests')
    @patch('power_benchmarking_suite.premium.PREMIUM_CONFIG_FILE')
    def test_verify_with_active_subscription(self, mock_file, mock_requests, tmp_path):
        """Test verification with active subscription"""
        # Setup
        config_dir = tmp_path / ".power_benchmarking"
        config_dir.mkdir()
        config_file = config_dir / "premium_config.json"
        config_file.write_text('{"tier": "free"}')
        
        mock_file.exists.return_value = True
        mock_file.__str__.return_value = str(config_file)
        
        # Mock response with active subscription
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"status": "active", "id": "sub_123"}]
        }
        mock_requests.get.return_value = mock_response
        
        # Import after patching
        from power_benchmarking_suite.premium import PremiumFeatures
        
        with patch('power_benchmarking_suite.premium.PREMIUM_CONFIG_FILE', config_file):
            pf = PremiumFeatures()
            result = pf.verify_polar_entitlement()
            
            assert result is True
            assert pf.tier == "premium"
    
    @patch('power_benchmarking_suite.premium.requests')
    def test_verify_with_invalid_token(self, mock_requests):
        """Test verification with 401 response"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_requests.get.return_value = mock_response
        
        from power_benchmarking_suite.premium import PremiumFeatures
        
        with patch.dict(os.environ, {"POLAR_API_KEY": "invalid_token"}):
            pf = PremiumFeatures()
            result = pf.verify_polar_entitlement()
            
            # Should return False on auth failure
            assert result is False
    
    def test_is_premium_with_env_variable(self):
        """Test is_premium returns True when POLAR_API_KEY is set"""
        from power_benchmarking_suite.premium import PremiumFeatures
        
        with patch.dict(os.environ, {"POLAR_API_KEY": "test_token_123"}):
            pf = PremiumFeatures()
            assert pf.is_premium() is True
    
    def test_is_premium_without_token(self):
        """Test is_premium returns cached tier when no token"""
        from power_benchmarking_suite.premium import PremiumFeatures
        
        # Clear env
        env_backup = os.environ.get("POLAR_API_KEY")
        if "POLAR_API_KEY" in os.environ:
            del os.environ["POLAR_API_KEY"]
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                pf = PremiumFeatures()
                pf.tier = "premium"  # Simulate cached state
                assert pf.is_premium() is True
        finally:
            if env_backup:
                os.environ["POLAR_API_KEY"] = env_backup
    
    @patch('power_benchmarking_suite.premium.requests')
    def test_verify_network_timeout_uses_cache(self, mock_requests):
        """Test that network timeout falls back to cached state"""
        import requests as req
        
        mock_requests.exceptions.Timeout = req.exceptions.Timeout
        mock_requests.get.side_effect = req.exceptions.Timeout()
        
        from power_benchmarking_suite.premium import PremiumFeatures
        
        with patch.dict(os.environ, {"POLAR_API_KEY": "test_token"}):
            pf = PremiumFeatures()
            pf.tier = "premium"  # Cached as premium
            
            # Should use cached state on timeout
            result = pf.verify_polar_entitlement()
            assert result is True  # Uses cached tier
    
    @patch('power_benchmarking_suite.premium.requests')
    def test_verify_clears_on_401(self, mock_requests):
        """Test that invalid token clears cached entitlement"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_requests.get.return_value = mock_response
        
        from power_benchmarking_suite.premium import PremiumFeatures
        
        with patch.dict(os.environ, {"POLAR_API_KEY": "invalid_token"}):
            pf = PremiumFeatures()
            pf.tier = "premium"
            
            pf.verify_polar_entitlement()
            
            # Tier should be cleared after 401
            assert pf.tier == "free"


class TestDeviceLinkFlow:
    """Test CLI activation polling flow"""
    
    def test_poll_activation_function_exists(self):
        """Test that _poll_activation function exists"""
        from power_benchmarking_suite.commands.premium_cmd import _poll_activation
        assert callable(_poll_activation)
    
    @patch('power_benchmarking_suite.commands.premium_cmd.requests')
    def test_poll_activation_calls_status_endpoint(self, mock_requests):
        """Test that activation polling hits the device-codes status endpoint"""
        from power_benchmarking_suite.commands.premium_cmd import _poll_activation
        
        # Mock GET response to simulate not-yet-activated code
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response
        
        result = _poll_activation("TEST-1234")
        
        # It should attempt to call the status endpoint at least once
        assert mock_requests.get.called
        called_url = mock_requests.get.call_args[0][0]
        assert "TEST-1234" in called_url
        assert result in [0, 1]


class TestEmailTemplate:
    """Test activation email template"""
    
    def test_activation_template_exists(self):
        """Test that activation email template exists"""
        from power_benchmarking_suite.marketing.email_templates import EmailTemplates
        
        templates = EmailTemplates()
        template = templates.get_template("activation")
        
        assert template is not None
        assert "activation" in template.html.lower()
        assert "{{ code }}" in template.html
        assert "{{ activation_url }}" in template.html
    
    def test_activation_template_renders(self):
        """Test that activation template renders correctly"""
        from power_benchmarking_suite.marketing.email_templates import EmailTemplates
        
        templates = EmailTemplates()
        template = templates.get_template("activation")
        
        rendered = template.render({
            "code": "ABCD-1234",
            "activation_url": "https://example.com/activate?code=ABCD-1234",
            "contact_name": "John"
        })
        
        assert "ABCD-1234" in rendered
        assert "https://example.com/activate" in rendered
        assert "John" in rendered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
