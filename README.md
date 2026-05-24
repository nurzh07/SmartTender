# SmartTender - Корпоративная платформа для автоматизации тендеров

## Описание проекта

SmartTender — корпоративная веб-платформа для полной цифровизации внутренних процессов закупок и тендеров казахстанских компаний. Проект разработан в рамках учебной дисциплины "Практика 2 — Создание внутрикорпоративных проектов".

## Технологический стек

### Backend
- **Python 3.12** + **FastAPI** — быстрый асинхронный фреймворк с автоматической OpenAPI документацией
- **PostgreSQL 16** — реляционная база данных для сложных связей
- **Redis 7** — кэширование + Celery broker
- **Celery 5** — фоновые задачи
- **Alembic** — миграции базы данных

### Аутентификация
- **JWT** (access token 15 мин + refresh token 30 дней)
- **Role-Based Access Control (RBAC)** — 5 ролей пользователей

### Контейнеризация
- **Docker** + **Docker Compose** — единая команда для запуска всех сервисов

## Архитектура

Проект использует **Modular Monolith** архитектуру:

```
smarttender/
├── app/
│   ├── api/              # API роутеры
│   │   ├── auth.py       # Аутентификация
│   │   ├── tenders.py    # Тендеры
│   │   └── users.py      # Пользователи
│   ├── core/             # Ядро системы
│   │   ├── security.py   # JWT токены
│   │   ├── deps.py       # Зависимости
│   │   └── redis_client.py
│   ├── models/           # SQLAlchemy модели
│   │   ├── user.py
│   │   ├── department.py
│   │   ├── tender.py
│   │   ├── category.py
│   │   └── proposal.py
│   ├── schemas/          # Pydantic схемы
│   ├── tasks/            # Celery задачи
│   ├── config.py         # Конфигурация
│   ├── database.py       # Подключение к БД
│   └── main.py           # Точка входа FastAPI
├── alembic/              # Миграции БД
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Роли пользователей

| Роль | Описание |
|------|----------|
| Superadmin | Все права, настройка компании, управление пользователями |
| Procurement Manager | Создание тендеров, утверждение поставщиков, контракты |
| Department Head | Утверждение/отклонение заявок своего отдела |
| Employee | Создание заявки на закупку, отслеживание статуса |
| Supplier | Участие в тендерах, коммерческие предложения |

## Статус реализации (1–2 апта)

| Апта | Критерий | Статус |
|------|----------|--------|
| 1 | docker-compose up, README, FastAPI каркас | ✅ |
| 2 | PostgreSQL + миграции, JWT, Redis кэш, CRUD | ✅ |

Архитектура: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
Апталық есеп: [docs/WEEK2_REPORT.md](docs/WEEK2_REPORT.md)

## Быстрый старт

### Требования
- Docker и Docker Compose
- Python 3.12+ (для локальной разработки)

### Запуск через Docker Compose

1. Клонировать репозиторий:
```bash
git clone <repository-url>
cd smarttender
```

2. Создать .env файл (скопировать из .env.example):
```bash
cp .env.example .env
```

3. Запустить все сервисы (миграции и seed автоматты):
```bash
docker compose up -d --build
```

4. API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Демо-аккаунты (после seed)

| Email | Пароль | Роль |
|-------|--------|------|
| admin@smarttender.kz | admin123 | superadmin |
| manager@smarttender.kz | manager123 | procurement_manager |
| supplier@smarttender.kz | supplier123 | supplier |

### Локальная разработка

1. Создать виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настроить переменные окружения в .env файле

4. Запустить PostgreSQL и Redis через Docker:
```bash
docker-compose up -d smarttender_db smarttender_redis
```

5. Применить миграции:
```bash
alembic upgrade head
```

6. Применить миграции и seed:
```bash
alembic upgrade head
python scripts/seed.py
```

7. Запустить FastAPI:
```bash
uvicorn app.main:app --reload
```

### Тесты

```bash
pip install -r requirements.txt
pytest
```

## API Эндпоинты

### Аутентификация
- `POST /api/auth/register` — Регистрация пользователя
- `POST /api/auth/login` — Вход (получение токенов)
- `POST /api/auth/refresh` — Обновление access токена

### Тендеры
- `POST /api/tenders/` — Создание тендера
- `GET /api/tenders/` — Список (пагинация `page`, фильтр `status`, Redis кэш, заголовок `X-Cache`)
- `GET /api/tenders/{id}` — Детали тендера
- `PATCH /api/tenders/{id}` — Обновление тендера
- `PATCH /api/tenders/{id}/status` — Изменение статуса
- `DELETE /api/tenders/{id}` — Удаление тендера

### Предложения
- `POST /api/tenders/{id}/proposals` — Отправить предложение (роль supplier)
- `GET /api/tenders/{id}/proposals` — Список предложений

### Категории и отделы
- `GET /api/categories/` — Справочник (кэш 1 час)
- `POST /api/categories/` — Создать категорию
- `GET /api/departments/` — Список отделов

### Пользователи
- `GET /api/users/me` — Текущий пользователь
- `GET /api/users/` — Список пользователей (только superadmin)
- `GET /api/users/{id}` — Детали пользователя
- `PATCH /api/users/{id}` — Обновление пользователя

## Статусы тендеров

- `DRAFT` — Черновик
- `PUBLISHED` — Опубликован
- `EVALUATION` — Оценка предложений
- `AWARDED` — Победитель определен
- `CLOSED` — Закрыт

## Статусы предложений

- `PENDING` — На рассмотрении
- `ACCEPTED` — Принято
- `REJECTED` — Отклонено

## Кэширование (Redis)

Стратегия кэширования:
- Активные тендеры: `tenders:active:page:{n}` — TTL 5 минут
- Категории: `categories:all` — TTL 1 час
- Рейтинг поставщиков: `supplier:rating:{id}` — TTL 30 минут
- Сессии пользователей: `session:{user_id}` — TTL 15 минут
- Бюджетная аналитика: `analytics:budget:{year}:{month}` — TTL 1 день

## Фоновые задачи (Celery)

- Отправка email уведомлений
- Генерация PDF отчетов
- Импорт тендеров из госзакупки.kz
- Автоматические напоминания о дедлайнах

## Структура базы данных

### Основные таблицы
- `users` — Пользователи
- `departments` — Отделы
- `categories` — Категории товаров/услуг
- `tenders` — Тендеры
- `tender_proposals` — Предложения поставщиков

## Безопасность

- Все секретные ключи в .env файле
- CORS: только разрешенные домены
- Rate Limiting: 100 запросов/минут с IP через Redis
- SQL Injection защита через SQLAlchemy ORM
- Пароли хешируются через bcrypt

## CI/CD (план)

- **CI**: ruff lint → pytest → coverage (минимум 40%)
- **Build**: Docker image build + push в Docker Hub
- **CD**: SSH деплой на VPS + docker-compose up

## Команда проекта

- DevOps инженер — Docker, CI/CD, VPS деплой
- Backend разработчик — FastAPI, JWT, RBAC, тендер API
- DB архитектор — PostgreSQL схема, индексы, транзакции
- Async/Интеграция разработчик — Celery, Telegram API, отчеты

## Лицензия

Учебный проект для университета

## Контакты

SmartTender команда | Практика 2, 2025
