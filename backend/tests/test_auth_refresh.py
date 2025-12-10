import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from app.services.schwab_auth import SchwabAuthService
from app.models.auth_token import AuthToken
from app.core.security import encrypt_token

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def valid_auth_token():
    token = AuthToken()
    token.access_token = encrypt_token("valid_access")
    token.refresh_token = encrypt_token("valid_refresh")
    token.expires_at = datetime.utcnow() + timedelta(hours=1)
    return token

@pytest.fixture
def expired_auth_token():
    token = AuthToken()
    token.access_token = encrypt_token("expired_access")
    token.refresh_token = encrypt_token("valid_refresh")
    token.expires_at = datetime.utcnow() - timedelta(minutes=10)
    return token

@pytest.mark.anyio
async def test_get_active_token_valid(mock_db, valid_auth_token):
    mock_db.query.return_value.first.return_value = valid_auth_token
    
    token = await SchwabAuthService.get_active_token(mock_db)
    
    assert token == "valid_access"

@pytest.mark.anyio
async def test_get_active_token_expired(mock_db, expired_auth_token):
    mock_db.query.return_value.first.return_value = expired_auth_token
    
    # Mock refresh_access_token to avoid actual API call and DB updates in this test
    # But since we want to test the flow, we can mock httpx instead.
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Create a MagicMock for the response, since json() and raise_for_status() are sync
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_in": 1800,
            "token_type": "Bearer"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        token = await SchwabAuthService.get_active_token(mock_db)
        
        assert token == "new_access"
        mock_post.assert_called_once()
        # Verify store_tokens was called (implied by success, but we can check side effects on mock_db)
        # However, SchwabAuthService.store_tokens creates a NEW AuthToken if not found, 
        # or updates existing. Our mock_db.query().first() returns the object.
        # Ideally we should verify 'add' or 'commit' was called.
        mock_db.commit.assert_called()

@pytest.mark.anyio
async def test_refresh_access_token_success(mock_db, expired_auth_token):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "refreshed_access",
            "refresh_token": "refreshed_refresh",
            "expires_in": 1800
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        token = await SchwabAuthService.refresh_access_token(mock_db, expired_auth_token)
        
        assert token == "refreshed_access"
        mock_db.commit.assert_called()
