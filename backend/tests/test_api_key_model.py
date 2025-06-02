"""
Unit tests for APIKey model and encryption service
"""

import pytest
import os
from unittest.mock import patch
from models.api_key import APIKey, APIKeyType
from models.user import User, UserRole
from services.encryption import EncryptionService

class TestEncryptionService:
    """Test encryption service functionality"""
    
    def test_encryption_service_init_requires_key(self):
        """Test that encryption service requires ENCRYPTION_KEY environment variable"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ENCRYPTION_KEY environment variable is required"):
                EncryptionService()
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-key-for-testing'}):
            service = EncryptionService()
            
            original_value = "sk-test-api-key-12345"
            encrypted = service.encrypt(original_value)
            decrypted = service.decrypt(encrypted)
            
            assert decrypted == original_value
            assert encrypted != original_value
    
    def test_encrypt_empty_value_raises_error(self):
        """Test that encrypting empty value raises error"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-key-for-testing'}):
            service = EncryptionService()
            
            with pytest.raises(ValueError, match="Cannot encrypt empty value"):
                service.encrypt("")
    
    def test_decrypt_invalid_value_raises_error(self):
        """Test that decrypting invalid value raises error"""
        with patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-key-for-testing'}):
            service = EncryptionService()
            
            with pytest.raises(ValueError, match="Invalid encrypted value"):
                service.decrypt("invalid-encrypted-value")

class TestAPIKeyModel:
    """Test APIKey model functionality"""
    
    def test_api_key_creation(self):
        """Test basic APIKey model creation"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI,
            is_active=True
        )
        
        assert api_key.user_id == "test-user-id"
        assert api_key.name == "OpenAI Key"
        assert api_key.key_type == APIKeyType.OPENAI
        assert api_key.is_active is True
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-key-for-testing'})
    def test_set_and_get_api_key_value(self):
        """Test setting and getting encrypted API key value"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI
        )
        
        original_key = "sk-test-api-key-12345"
        api_key.set_api_key_value(original_key)
        
        # Verify the value is encrypted (not stored in plain text)
        assert api_key.encrypted_value != original_key
        
        # Verify we can decrypt it back
        decrypted_key = api_key.get_api_key_value()
        assert decrypted_key == original_key
    
    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test-key-for-testing'})
    def test_get_masked_value(self):
        """Test getting masked version of API key"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI
        )
        
        api_key.set_api_key_value("sk-test-api-key-12345")
        masked = api_key.get_masked_value()
        
        # Should show first 4 and last 4 characters
        assert masked.startswith("sk-t")
        assert masked.endswith("2345")
        assert "*" in masked
    
    def test_validate_key_type(self):
        """Test API key type validation"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI
        )
        
        assert api_key.validate_key_type() is True
        
        # Test invalid key type
        api_key.key_type = "invalid-type"
        assert api_key.validate_key_type() is False
    
    def test_validate_api_key_format(self):
        """Test API key format validation"""
        # Test OpenAI key format
        assert APIKey.validate_api_key_format(APIKeyType.OPENAI, "sk-test123456789012345") is True
        assert APIKey.validate_api_key_format(APIKeyType.OPENAI, "invalid-key") is False
        
        # Test Anthropic key format
        assert APIKey.validate_api_key_format(APIKeyType.ANTHROPIC, "sk-ant-test123456789012345") is True
        assert APIKey.validate_api_key_format(APIKeyType.ANTHROPIC, "sk-test123") is False
        
        # Test empty key
        assert APIKey.validate_api_key_format(APIKeyType.OPENAI, "") is False
        assert APIKey.validate_api_key_format(APIKeyType.OPENAI, "   ") is False
    
    def test_soft_delete(self):
        """Test soft delete functionality"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI,
            is_active=True
        )
        
        api_key.soft_delete()
        assert api_key.is_active is False
    
    def test_is_owned_by(self):
        """Test ownership validation"""
        api_key = APIKey(
            user_id="test-user-id",
            name="OpenAI Key",
            key_type=APIKeyType.OPENAI
        )
        
        assert api_key.is_owned_by("test-user-id") is True
        assert api_key.is_owned_by("different-user-id") is False 