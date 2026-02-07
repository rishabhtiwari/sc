#!/usr/bin/env python3
"""
Generate Encryption Key for Master App Management

This script generates a Fernet encryption key for encrypting
social media app secrets and access tokens.

Usage:
    python scripts/generate_encryption_key.py
"""

from cryptography.fernet import Fernet

def generate_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    return key.decode()

if __name__ == '__main__':
    print("=" * 70)
    print("🔐 Encryption Key Generator for Master App Management")
    print("=" * 70)
    print()
    
    key = generate_key()
    
    print("✅ Generated Encryption Key:")
    print()
    print(f"    {key}")
    print()
    print("📝 Instructions:")
    print()
    print("1. Copy the key above")
    print("2. Add it to your .env file:")
    print()
    print(f"   ENCRYPTION_KEY={key}")
    print()
    print("3. Restart your services")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Keep this key secret!")
    print("   - Never commit it to version control!")
    print("   - If you lose this key, you won't be able to decrypt existing data!")
    print("   - Store it securely (e.g., password manager, secrets manager)")
    print()
    print("=" * 70)

