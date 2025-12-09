from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_campaigns():
    return []

@router.get("/{id}")
def get_campaign(id: str):
    return {}
