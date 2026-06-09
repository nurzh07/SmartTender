# Апталық есеп — 1-апта

## Жоба тақырыбы

**SmartTender** — Қазақстан компанияларының ішкі сатып алу және тендер процестерін автоматтандыру платформасы.

## Бизнес-процестер

1. Қызметкер тендер өтінімін жасайды (DRAFT)
2. Бөлім басшысы → сатып алу менеджері бекітеді (approval workflow)
3. Тендер жарияланады, жеткізушілер ұсыныс жібереді
4. Бағалау және жеңімпазды таңдау
5. Есептер (PDF/Excel) және хабарландырулар

## Архитектуралық шешім

**Modular Monolith** — бір репозиторий, модульдік құрылым, кейін микросервиске бөлуге дайын.

Толық схема: `docs/ARCHITECTURE.md`

| Қабат | Технология |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite |
| API | FastAPI (Python 3.12) |
| DB | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Фон тапсырмалар | Celery + Celery Beat |
| Контейнерлеу | Docker + Docker Compose |

## Docker қызметтері

```bash
docker compose up -d --build
```

| Қызмет | Порт | Мақсаты |
|--------|------|---------|
| smarttender_api | 8000 | REST API, Swagger |
| smarttender_frontend | 3000 | React SPA |
| smarttender_db | 5432 | PostgreSQL |
| smarttender_redis | 6379 | Кэш + Celery broker |
| smarttender_worker | — | Celery worker |
| smarttender_beat | — | Cron тапсырмалары |

## GitHub репозиторий

- Бірлескен жұмыс: feature branches + pull requests
- CI/CD: `.github/workflows/ci-cd.yml` (lint → test → Docker build → deploy)

## Негізгі API модульдері (каркас)

- `/api/auth` — JWT аутентификация
- `/api/tenders` — тендер CRUD
- `/api/proposals` — ұсыныстар
- `/api/categories`, `/api/departments`, `/api/users`
- `/docs` — Swagger/OpenAPI құжаттамасы

## Демо іске қосу

```bash
cp .env.example .env
docker compose up -d --build
```

API: http://localhost:8000/docs  
Frontend: http://localhost:3000

## Келесі апта (2)

- Redis кэштеу, индекстер, N+1 оңтайландыру
- PostgreSQL триггерлері және транзакциялар
