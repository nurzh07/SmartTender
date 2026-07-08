#!/bin/sh
set -e
# alembic upgrade head
# python scripts/seed.py || echo "Seed skipped or failed (non-fatal)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
