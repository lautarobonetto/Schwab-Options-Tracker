import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from app.db.base import Base
from app.models.auth_token import AuthToken
from app.services.schwab_auth import SchwabAuthService
from app.core.security import decrypt_token, encrypt_token
from app.core.config import settings
from unittest.mock import MagicMock, patch, AsyncMock

# Override DB path
settings.SQLITE_DB_PATH = "verify_uc01.db"

# Init DB
engine = create_engine(f"sqlite:///{settings.SQLITE_DB_PATH}")
Base.metadata.create_all(bind=engine)
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

async def verify_async():
    print("1. Testing Encryption...")
    original = "secret_token_123"
    encrypted = encrypt_token(original)
    decrypted = decrypt_token(encrypted)
    assert original != encrypted
    assert original == decrypted
    print("   [OK] Encryption/Decryption works.")
    
    print("2. Testing Schwab Auth Flow (Async Mock)...")
    mock_response = {
        "access_token": "access_123",
        "refresh_token": "refresh_123",
        "expires_in": 1800,
        "token_type": "Bearer",
        "id_token": "id_123"
    }
    
    # Mock httpx.AsyncClient
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.__aenter__.return_value = mock_instance
        
        # Mock response
        mock_resp_obj = MagicMock()
        mock_resp_obj.json.return_value = mock_response
        mock_resp_obj.raise_for_status = MagicMock()
        
        mock_instance.post = AsyncMock(return_value=mock_resp_obj)
        
        # Test exchange
        await SchwabAuthService.exchange_code_for_token(db, "fake_code")
        
        # Verify DB
        token_entry = db.query(AuthToken).first()
        assert token_entry is not None
        print("   [OK] Token saved to DB.")
        
        # Verify stored values are encrypted
        assert token_entry.access_token != "access_123"
        print("   [OK] Access Token is encrypted in DB.")
        
        # Verify decryption
        assert decrypt_token(token_entry.access_token) == "access_123"
        print("   [OK] Access Token decrypts correctly.")

    print("\nSUCCESS: UC-01 Verification Passed!")

if __name__ == "__main__":
    try:
        asyncio.run(verify_async())
    finally:
        db.close()
        if os.path.exists("verify_uc01.db"):
            os.remove("verify_uc01.db")
