from fastapi import APIRouter

router = APIRouter()

@router.post("/history")
def sync_history():
    return {"msg": "Trigger background sync"}

@router.get("/status")
def sync_status():
    return {"status": "idle"}
