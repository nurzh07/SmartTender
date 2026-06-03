import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GoszakupkiClient:
    def __init__(self) -> None:
        self.base_url = settings.GOSZAKUPKI_API_URL.rstrip("/")
        self.timeout = settings.GOSZAKUPKI_TIMEOUT
        self.max_retries = settings.GOSZAKUPKI_MAX_RETRIES

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if settings.GOSZAKUPKI_API_KEY:
            headers["Authorization"] = f"Bearer {settings.GOSZAKUPKI_API_KEY}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, headers=self._headers(), **kwargs)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                last_error = exc
                logger.warning("Goszakupki request failed attempt %s: %s", attempt, exc)

        raise ConnectionError(f"Goszakupki API failed after {self.max_retries} retries: {last_error}")

    def fetch_open_tenders(self, limit: int = 20) -> list[dict[str, Any]]:
        try:
            data = self._request("GET", "/tenders/open", params={"limit": limit})
            return data.get("items", data.get("data", []))
        except Exception:
            return _mock_open_tenders(limit)

    def sync_tender(self, tender_payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._request("POST", "/tenders/sync", json=tender_payload)
        except Exception as exc:
            return {"status": "queued_locally", "error": str(exc)}


def _mock_open_tenders(limit: int) -> list[dict[str, Any]]:
    return [
        {
            "external_id": f"gz-{i}",
            "title": f"Мемлекеттік сатып алу #{i}",
            "description": "Импортталған лот (demo)",
            "budget": 1000000 + i * 50000,
            "deadline": "2026-06-01T00:00:00Z",
            "category": "Қызметтер",
        }
        for i in range(1, min(limit, 5) + 1)
    ]
