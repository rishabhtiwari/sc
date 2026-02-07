"""
Encryption utilities for securing sensitive data
Uses Fernet (symmetric encryption) to encrypt/decrypt secrets and tokens
Each customer has their own encryption key stored in the database
"""

import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def encrypt_value(plaintext, encryption_key):
    """
    Encrypt a plaintext string using customer-specific encryption key

    Args:
        plaintext (str): The value to encrypt
        encryption_key (str): Customer's encryption key

    Returns:
        str: Encrypted value (base64 encoded)
    """
    if not plaintext:
        return None

    if not encryption_key:
        raise ValueError("Encryption key is required")

    try:
        # Convert key to bytes if string
        key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        f = Fernet(key_bytes)

        # Convert to bytes if string
        plaintext_bytes = plaintext.encode() if isinstance(plaintext, str) else plaintext

        # Encrypt
        encrypted_bytes = f.encrypt(plaintext_bytes)

        # Return as string
        return encrypted_bytes.decode()

    except Exception as e:
        logger.error(f"❌ Encryption failed: {e}")
        raise


def decrypt_value(encrypted_text, encryption_key):
    """
    Decrypt an encrypted string using customer-specific encryption key

    Args:
        encrypted_text (str): The encrypted value (base64 encoded)
        encryption_key (str): Customer's encryption key

    Returns:
        str: Decrypted plaintext value
    """
    if not encrypted_text:
        return None

    if not encryption_key:
        raise ValueError("Encryption key is required")

    try:
        # Convert key to bytes if string
        key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        f = Fernet(key_bytes)

        # Convert to bytes if string
        encrypted_bytes = encrypted_text.encode() if isinstance(encrypted_text, str) else encrypted_text

        # Decrypt
        decrypted_bytes = f.decrypt(encrypted_bytes)

        # Return as string
        return decrypted_bytes.decode()

    except Exception as e:
        logger.error(f"❌ Decryption failed: {e}")
        raise


def generate_encryption_key():
    """
    Generate a new Fernet encryption key
    
    Returns:
        str: New encryption key (base64 encoded)
    """
    key = Fernet.generate_key()
    return key.decode()


# Test encryption/decryption on module load
if __name__ == "__main__":
    # Test
    test_value = "my-secret-app-key-12345"
    print(f"Original: {test_value}")
    
    encrypted = encrypt_value(test_value)
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_value(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert test_value == decrypted, "Encryption/Decryption test failed!"
    print("✅ Encryption test passed!")
    
    # Generate new key
    new_key = generate_encryption_key()
    print(f"\nNew encryption key: {new_key}")
    print("Add this to your .env file as: ENCRYPTION_KEY={new_key}")

