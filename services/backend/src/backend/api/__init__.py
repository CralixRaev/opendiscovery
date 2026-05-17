from fastapi import APIRouter

from backend.api import auth, system


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)

system_router = APIRouter()
system_router.include_router(system.router)
