# Апталық есеп — 5-апта (Автоматтандырылған тестілеу және CI/CD)

## 1) Орындалған тапсырмалар мен архитектуралық шешімдер

- **Тесттер кеңейтілді**
  - Жаңа файл: `tests/test_week5_business_logic.py`
  - Тексерілетін логика:
    - Goszakupki fallback mock,
    - sync кезінде connection error өңдеу,
    - RBAC рұқсат тексерісі.
- **Бұрыннан бар тесттермен бірге**
  - `tests/test_security.py` (JWT/password)
  - `tests/test_cache.py` (Redis cache layer)
- **CI сапа қақпасы**
  - `pytest --cov=app --cov-fail-under=40`
  - `ruff check` + `ruff format --check`

## 2) Коммит/PR және CI/CD статусы

- Workflow: `.github/workflows/ci-cd.yml`
- Job тізбегі:
  1. `lint`
  2. `test` (Postgres + Redis service)
  3. `build` (Docker image push)
  4. `deploy` (VPS via SSH)
- Өлшем: **coverage fail-under = 40%**.

## 3) Техникалық қиындықтар және шешімдер

- **Локалды ортада pytest plugin конфликті**
  - Шешім: CI ортасын негізгі source of truth ретінде пайдалану;
  - Docker/CI python environment-те тест жүргізу.
- **Интеграциялық тәуелділіктер (Postgres/Redis)**
  - Шешім: GitHub Actions service containers пайдалану.

## 4) Келесі аптаға спринт жоспары (6-апта)

- Compose-ты production-friendly ету (`.env`-тен параметр оқу).
- Құпия мәндерді hardcode етпеу.
- Deploy операциясын тек `main` үшін қалдыру (бар конфигті валидациялау).
