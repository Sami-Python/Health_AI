"""
Encryption Helper for Sensitive User Data
Uses Fernet (AES-256) symmetric encryption.

CRITICAL: ENCRYPTION_KEY must be set in environment variables.
Without the key, encrypted data cannot be recovered.
"""
import os
from cryptography.fernet import Fernet
from typing import Optional


def _get_cipher():
    """Gets Fernet cipher instance from environment key."""
    key = os.getenv("ENCRYPTION_KEY")
    
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY not found in environment. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Key should be bytes
    if isinstance(key, str):
        key = key.encode()
    
    return Fernet(key)


def encrypt_text(plaintext: str) -> str:
    """
    Encrypts plaintext string using Fernet (AES-256).
    
    Args:
        plaintext: Text to encrypt (e.g., password)
        
    Returns:
        Base64-encoded encrypted string (safe for Firestore storage)
        
    Example:
        >>> encrypted = encrypt_text("my_password")
        >>> print(encrypted)
        'gAAAAABhX...'
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty string")
    
    cipher = _get_cipher()
    encrypted_bytes = cipher.encrypt(plaintext.encode())
    return encrypted_bytes.decode()  # Return as string for Firestore


def decrypt_text(encrypted: str) -> str:
    """
    Decrypts Fernet-encrypted string.
    
    Args:
        encrypted: Base64-encoded encrypted string
        
    Returns:
        Original plaintext
        
    Raises:
        cryptography.fernet.InvalidToken: If data is corrupted or key is wrong
        
    Example:
        >>> decrypted = decrypt_text('gAAAAABhX...')
        >>> print(decrypted)
        'my_password'
    """
    if not encrypted:
        raise ValueError("Cannot decrypt empty string")
    
    cipher = _get_cipher()
    decrypted_bytes = cipher.decrypt(encrypted.encode())
    return decrypted_bytes.decode()


# Convenience aliases for clarity
encrypt_password = encrypt_text
decrypt_password = decrypt_text


def generate_new_key() -> str:
    """
    Generates a new Fernet encryption key.
    
    WARNING: Only use this once when setting up a new environment.
    Changing the key will make all existing encrypted data unrecoverable.
    
    Returns:
        Base64-encoded encryption key (44 characters)
    """
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    # Self-test (only runs if executed directly)
    print("Encryption Helper Self-Test\n")
    
    # Check if key exists
    if not os.getenv("ENCRYPTION_KEY"):
        print("WARNING: ENCRYPTION_KEY not set. Generating a new one:")
        new_key = generate_new_key()
        print(f"   Add this to your .env file:")
        print(f"   ENCRYPTION_KEY={new_key}\n")
    else:
        # Test encryption/decryption
        test_password = "test_garmin_password_123"
        print(f"Original:  {test_password}")
        
        encrypted = encrypt_password(test_password)
        print(f"Encrypted: {encrypted[:50]}...")
        
        decrypted = decrypt_password(encrypted)
        print(f"Decrypted: {decrypted}")
        
        if decrypted == test_password:
            print("\nSUCCESS: Encryption/Decryption working correctly!")
        else:
            print("\nERROR: Decryption failed!")

