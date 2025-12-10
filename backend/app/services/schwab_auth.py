import base64
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.auth_token import AuthToken
from app.core.security import encrypt_token

class SchwabAuthService:
    BASE_URL = "https://api.schwabapi.com/v1/oauth"
    
    @staticmethod
    def generate_auth_url() -> str:
        """Generates the Schwab authorization URL."""
        return (
            f"{SchwabAuthService.BASE_URL}/authorize?"
            f"client_id={settings.SCHWAB_APP_KEY}&"
            f"redirect_uri={settings.REDIRECT_URI}&"
            "response_type=code"
        )

    @staticmethod
    async def exchange_code_for_token(db: Session, code: str) -> dict:
        """Exchanges the authorization code for an access token."""
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{settings.SCHWAB_APP_KEY}:{settings.SCHWAB_APP_SECRET}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.REDIRECT_URI
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{SchwabAuthService.BASE_URL}/token", headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
        
        SchwabAuthService.store_tokens(db, token_data)
        return token_data

    @staticmethod
    def store_tokens(db: Session, token_data: dict):
        """Encrypts and stores tokens in the database."""
        # Calculate expiration time (usually expires_in is in seconds)
        expires_in = token_data.get("expires_in", 1800)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if we already have a token row (we assume single user for now)
        auth_token = db.query(AuthToken).first()
        if not auth_token:
            auth_token = AuthToken()
            db.add(auth_token)
        
        auth_token.access_token = encrypt_token(token_data.get("access_token"))
        auth_token.refresh_token = encrypt_token(token_data.get("refresh_token"))
        auth_token.id_token = encrypt_token(token_data.get("id_token", ""))
        auth_token.token_type = token_data.get("token_type", "Bearer")
        auth_token.expires_at = expires_at
        
        db.commit()
        db.refresh(auth_token)

    @staticmethod
    def store_tokens(db: Session, token_data: dict):
        """Encrypts and stores tokens in the database."""
        # Calculate expiration time (usually expires_in is in seconds)
        expires_in = token_data.get("expires_in", 1800)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if we already have a token row (we assume single user for now)
        auth_token = db.query(AuthToken).first()
        if not auth_token:
            auth_token = AuthToken()
            db.add(auth_token)
        
        auth_token.access_token = encrypt_token(token_data.get("access_token"))
        auth_token.refresh_token = encrypt_token(token_data.get("refresh_token"))
        auth_token.id_token = encrypt_token(token_data.get("id_token", ""))
        auth_token.token_type = token_data.get("token_type", "Bearer")
        auth_token.expires_at = expires_at
        
        db.commit()
        db.refresh(auth_token)

    @staticmethod
    async def get_active_token(db: Session) -> str:
        """
        Retrieves a valid access token. 
        If it's expired or about to expire (< 5 mins), it refreshes it first.
        """
        auth_token = db.query(AuthToken).first()
        if not auth_token:
            return None

        # Check expiry (buffer of 5 minutes)
        if auth_token.expires_at <= datetime.utcnow() + timedelta(minutes=5):
            print("Token expired or close to expiry. Refreshing...")
            return await SchwabAuthService.refresh_access_token(db, auth_token)
        
        from app.core.security import decrypt_token
        return decrypt_token(auth_token.access_token)

    @staticmethod
    async def refresh_access_token(db: Session, auth_token: AuthToken) -> str:
        """Uses the refresh_token to obtain a new access_token."""
        from app.core.security import decrypt_token
        
        refresh_token_plain = decrypt_token(auth_token.refresh_token)
        if not refresh_token_plain:
            print("No refresh token available.")
            return None

        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{settings.SCHWAB_APP_KEY}:{settings.SCHWAB_APP_SECRET}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token_plain
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{SchwabAuthService.BASE_URL}/token", headers=headers, data=data)
                response.raise_for_status()
                token_data = response.json()
                
                # Update DB with new tokens
                SchwabAuthService.store_tokens(db, token_data)
                
                return token_data.get("access_token")
            except httpx.HTTPError as e:
                print(f"Failed to refresh token: {e}")
                # Ideally, log this error properly
                return None
