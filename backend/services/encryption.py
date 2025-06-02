"""
Encryption service for secure API key storage
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionService:
    """Service for encrypting and decrypting sensitive data like API keys"""
    
    def __init__(self):
        self._fernet: Fernet
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with key from environment"""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        
        # Derive a 32-byte key from the environment variable
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'salt_for_api_keys',  # In production, use random salt per key
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        self._fernet = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value and return base64 encoded result"""
        if not value:
            raise ValueError("Cannot encrypt empty value")
        
        try:
            encrypted_bytes = self._fernet.encrypt(value.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a base64 encoded encrypted value"""
        if not encrypted_value:
            raise ValueError("Cannot decrypt empty value")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            raise ValueError("Invalid encrypted value or wrong encryption key")
        except Exception as e:
            raise RuntimeError(f"Decryption failed: {str(e)}")
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted (base64 encoded)"""
        try:
            base64.urlsafe_b64decode(value)
            return True
        except:
            return False

# Global encryption service instance
encryption_service = EncryptionService() 