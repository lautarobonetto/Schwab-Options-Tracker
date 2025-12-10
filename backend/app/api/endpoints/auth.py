from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.services.schwab_auth import SchwabAuthService

router = APIRouter()

@router.get("/login")
def login():
    """Redirects the user to Schwab OAuth login."""
    auth_url = SchwabAuthService.generate_auth_url()
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def callback(code: str, db: Session = Depends(deps.get_db)):
    """Callback from Schwab OAuth."""
    try:
        token_data = await SchwabAuthService.exchange_code_for_token(db, code)
        return {"msg": "Authentication successful", "expires_in": token_data.get("expires_in")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
