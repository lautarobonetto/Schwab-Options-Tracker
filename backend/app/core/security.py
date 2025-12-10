from cryptography.fernet import Fernet
import base64
from app.core.config import settings

def get_fernet_key() -> bytes:
    """
    Derives a 32-byte URL-safe base64-encoded key from the SECRET_KEY.
    Fernet requires a 32-byte key.
    """
    # Simple derivation: pad or truncate SECRET_KEY to 32 bytes then urlsafe_b64encode
    # Note: In production, better key management is advised.
    key = settings.SECRET_KEY.encode()
    if len(key) < 32:
        key = key + b"=" * (32 - len(key))
    else:
        key = key[:32]
    return base64.urlsafe_b64encode(key)

_fernet = Fernet(get_fernet_key())

def encrypt_token(token: str) -> str:
    """Encrypts a token string."""
    if not token:
        return ""
    return _fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a token string."""
    if not encrypted_token:
        return ""
    try:
        return _fernet.decrypt(encrypted_token.encode()).decode()
    except Exception:
        # In case of decryption failure (e.g. key change), return empty or handle error
        return ""
