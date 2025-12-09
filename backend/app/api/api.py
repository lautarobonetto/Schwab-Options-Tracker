from fastapi import APIRouter
from app.api.endpoints import auth, data, campaigns

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(data.router, prefix="/sync", tags=["sync"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
