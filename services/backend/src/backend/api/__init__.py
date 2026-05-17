from fastapi import APIRouter

from backend.api import auth, scan_jobs, scanners, system


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(scanners.router)
api_router.include_router(scan_jobs.router)

system_router = APIRouter()
system_router.include_router(system.router)
