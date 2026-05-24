# Апталық есеп — 2-апта

## Орындалған тапсырмалар

1. **PostgreSQL** — кестелер, FK, Alembic миграциялары, композиттік индекстер
2. **JWT auth** — register, login, refresh (access 15 мин, refresh 30 күн)
3. **RBAC** — рөлдер бойынша endpoint қорғанысы
4. **Redis кэш** — тендерлер тізімі, санаттар; `X-Cache` заголовғы
5. **CRUD API** — tenders, proposals, categories, departments, users
6. **N+1** — `selectinload` тендерлер мен ұсыныстарда

## Демо тіркелгілер (seed)

| Email | Пароль | Рөл |
|-------|--------|-----|
| admin@smarttender.kz | admin123 | superadmin |
| manager@smarttender.kz | manager123 | procurement_manager |
| supplier@smarttender.kz | supplier123 | supplier |

## Кэш тесті (Swagger)

1. `GET /api/tenders?page=1&status=published` — бірінші сұрау: `X-Cache: MISS`
2. Қайталау — `X-Cache: HIT` (жауап уақыты ~2x жылдам)

## Келесі апта (3)

- Celery email/Telegram хабарландыру
- PDF есеп генерациясы
- Approval workflow
