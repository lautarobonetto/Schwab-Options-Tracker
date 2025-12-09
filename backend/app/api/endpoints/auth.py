from fastapi import APIRouter

router = APIRouter()

@router.get("/login")
def login():
    return {"msg": "Redirect to Schwab OAuth"}

@router.get("/callback")
def callback():
    return {"msg": "Handle callback"}
