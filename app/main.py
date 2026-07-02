from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import (
    approval,
    auth,
    categories,
    departments,
    integrations,
    notifications,
    odoo,
    proposals,
    reports,
    suppliers,
    tenders,
    users,
    webhooks,
)
from app.config import get_settings
from app.core.middleware import RateLimitMiddleware
from app.core.redis_client import redis_client
from app.database import SessionLocal
from app.services.storage import ensure_upload_dirs

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_dirs()
    try:
        redis_client.ping()
    except Exception:
        pass
    yield


app = FastAPI(
    redirect_slashes=False,
    title="SmartTender API",
    description="""
    ## SmartTender — Корпоративтік тендерлерді автоматтандыру платформасы
    
    Бұл API Қазақстан компанияларының ішкі сатып алу және тендер процестерін толық цифрландыруға арналған.
    
    ### Негізгі мүмкіндіктер:
    - **Аутентификация**: JWT access + refresh токендері, RBAC (5 рөл)
    - **Тендер**: CRUD, статус басқару, бекіту workflow
    - **Ұсыныстар**: Жеткізушілердің коммерциялық ұсыныстары
    - **Хабарландыру**: Email + Telegram арқылы автоматты хабарламалар
    - **Есептер**: PDF, Excel, бюджет аналитикасы
    - **Интеграция**: Госзакупки.kz API
    
    ### Рөлдер:
    - `superadmin` — Толық құқықтар
    - `buyer` — Тендер басқару
    - `department_head` — Бөлім бекітуі
    - `employee` — Өтінім жасау
    - `supplier` — Ұсыныс жіберу
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Аутентификация және авторизация (JWT, RBAC)"
        },
        {
            "name": "tenders",
            "description": "Тендерлер CRUD, статус басқару, кэштеу"
        },
        {
            "name": "proposals",
            "description": "Жеткізушілердің ұсыныстары"
        },
        {
            "name": "approval",
            "description": "Тендер бекіту workflow"
        },
        {
            "name": "reports",
            "description": "Есептер генерациясы (PDF, Excel, аналитика)"
        },
        {
            "name": "notifications",
            "description": "Хабарландырулар"
        },
        {
            "name": "integrations",
            "description": "Сыртқы API интеграциялары (Госзакупки.kz)"
        },
        {
            "name": "odoo",
            "description": "Odoo ERP интеграциясы (қызметкерлер синхрондау)"
        },
    ]
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(tenders.router, prefix="/api/tenders", tags=["tenders"])
app.include_router(approval.router, prefix="/api/tenders", tags=["approval"])
app.include_router(proposals.router, prefix="/api/tenders", tags=["proposals"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(departments.router, prefix="/api/departments", tags=["departments"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["suppliers"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(odoo.router, prefix="/api/odoo", tags=["odoo"])


@app.get("/")
async def root():
    return {
        "message": "SmartTender API",
        "version": "2.0.0",
        "docs": "/docs",
        "modules": ["auth", "tenders", "approval", "notifications", "reports", "goszakupki"],
    }


@app.get("/health")
async def health_check():
    redis_ok = False
    db_ok = False
    try:
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        db.close()
    return {
        "status": "healthy" if redis_ok and db_ok else "degraded",
        "redis": redis_ok,
        "database": db_ok,
    }
