import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import Config

from backend.api import api_router, system_router
from backend.database import lifespan


settings = Config()

app = FastAPI(title="OpenDiscovery Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(system_router)


def main() -> None:
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
