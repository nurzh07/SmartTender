# SmartTender — 3-бөлім функционалдық талаптар

## 3.1 Рөлдер (RBAC)

| Рөл | Endpoint мысалы |
|-----|-----------------|
| superadmin | Барлық API |
| procurement_manager | Статус, есеп, госзакупки |
| department_head | `POST /api/tenders/{id}/approve` (1-қадам) |
| employee | Тендер жасау, `POST .../submit` |
| supplier | Ұсыныс, файл жүктеу |

## 3.2.1 Auth

- `POST /api/auth/forgot-password` — Celery email
- `POST /api/auth/reset-password` — Redis token
- Rate limit: 100 req/min (Redis, `429`)

## 3.2.2 Тендер + бекіту

- Workflow: `submit` → dept head → procurement → **PUBLISHED**
- `POST /api/tenders/{id}/submit`
- `POST /api/tenders/{id}/approve` | `reject`
- `POST /api/tenders/{id}/proposals/upload` — файл
- Автобалл: баға + мерзім + рейтинг

## 3.2.3 Хабарландыру (Celery)

- Тендер жарияланды → email (+ Telegram дайын)
- Бекіту нәтижесі
- Дедлайн 3/1 күн (beat күн сайын)
- Жеңімпаз → `AWARDED` статусы

## 3.2.4 Есептер

- `POST /api/reports/generate`
- `GET /api/reports/{id}/download`
- PDF (reportlab), Excel (openpyxl)
- MinIO опционал (`USE_MINIO=true`)

## 3.2.5 Госзакупки.kz

- `POST /api/integrations/goszakupki/import`
- `GET /api/integrations/goszakupki/preview`
- `POST /api/webhooks/goszakupki`
- Timeout 5s, retry 3

## Docker

```bash
docker compose up -d --build
docker compose exec smarttender_api alembic upgrade head
```

## Демо аккаунттар

| Email | Пароль | Рөл |
|-------|--------|-----|
| employee@smarttender.kz | employee123 | employee |
| head@smarttender.kz | head123 | department_head |
| manager@smarttender.kz | manager123 | procurement_manager |
| supplier@smarttender.kz | supplier123 | supplier |
