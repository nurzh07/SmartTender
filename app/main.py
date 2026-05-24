from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, categories, departments, proposals, tenders, users
from app.config import get_settings
from app.core.redis_client import redis_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_client.ping()
    except Exception:
        pass
    yield


app = FastAPI(
    title="SmartTender API",
    description="Корпоративная платформа для автоматизации тендеров",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(tenders.router, prefix="/api/tenders", tags=["tenders"])
app.include_router(proposals.router, prefix="/api/tenders", tags=["proposals"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])


@app.get("/")
async def root():
    return {"message": "SmartTender API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False
    return {"status": "healthy", "redis": redis_ok}
