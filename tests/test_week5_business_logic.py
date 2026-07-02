from fastapi import HTTPException

from app.models.user import UserRole
from app.services.goszakupki_client import GoszakupkiClient, _mock_open_tenders


def test_mock_open_tenders_respects_limit():
    items = _mock_open_tenders(2)
    assert len(items) == 2
    assert items[0]["external_id"].startswith("gz-")


def test_fetch_open_tenders_fallback_to_mock(monkeypatch):
    client = GoszakupkiClient()

    def _raise_connection_error(*args, **kwargs):
        raise ConnectionError("upstream unavailable")

    monkeypatch.setattr(client, "_request", _raise_connection_error)
    data = client.fetch_open_tenders(limit=3)

    assert len(data) == 3
    assert data[0]["title"]


def test_sync_tender_returns_queued_on_connection_error(monkeypatch):
    client = GoszakupkiClient()

    def _raise_connection_error(*args, **kwargs):
        raise ConnectionError("down")

    monkeypatch.setattr(client, "_request", _raise_connection_error)
    result = client.sync_tender({"title": "T"})

    assert result["status"] == "queued_locally"
    assert result["error"] == "connection_failed"


def test_rbac_require_roles_denies_forbidden_user():
    import asyncio
    from app.core.rbac import require_roles

    checker = require_roles(UserRole.SUPERADMIN)

    class DummyUser:
        def __init__(self, role):
            self.role = role

    try:
        asyncio.run(checker(DummyUser(UserRole.EMPLOYEE)))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Expected HTTPException 403")
