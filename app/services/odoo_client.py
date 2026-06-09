import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OdooClient:
    """Odoo ERP жүйесімен интеграция үшін клиент."""

    def __init__(self) -> None:
        self.base_url = settings.ODOO_URL.rstrip("/")
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USERNAME
        self.password = settings.ODOO_PASSWORD
        self.timeout = settings.ODOO_TIMEOUT
        self.max_retries = settings.ODOO_MAX_RETRIES
        self._session_id: str | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, headers=self._headers(), **kwargs)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("Odoo request timeout attempt %s: %s", attempt, exc)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning("Odoo request failed attempt %s: %s", attempt, exc)
                if exc.response.status_code >= 500:
                    continue
                break
            except Exception as exc:
                last_error = exc
                logger.warning("Odoo request failed attempt %s: %s", attempt, exc)

        raise ConnectionError(f"Odoo API failed after {self.max_retries} retries: {last_error}")

    def authenticate(self) -> bool:
        """Odoo-да аутентификация жасау."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "login",
                    "args": [self.db, self.username, self.password],
                },
                "id": 1,
            }
            response = self._request("POST", "/web/session/authenticate", json=payload)
            self._session_id = response.get("result")
            return self._session_id is not None
        except Exception as exc:
            logger.error("Odoo authentication failed: %s", exc)
            return False

    def fetch_employees(self) -> list[dict[str, Any]]:
        """Odoo-дан қызметкерлер тізімін алу."""
        try:
            if not self._session_id and not self.authenticate():
                return []

            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.db,
                        self._session_id,
                        self.password,
                        "hr.employee",
                        "search_read",
                        [[["active", "=", True]]],
                        {"fields": ["name", "email", "department_id", "job_id"]},
                    ],
                },
                "id": 2,
            }
            response = self._request("POST", "/web/dataset/call_kw", json=payload)
            return response.get("result", [])
        except Exception as exc:
            logger.error("Failed to fetch employees from Odoo: %s", exc)
            return _mock_employees()

    def sync_employee(self, employee_data: dict[str, Any]) -> dict[str, Any]:
        """Қызметкер деректерін Odoo-ға синхрондау."""
        try:
            if not self._session_id and not self.authenticate():
                return {"status": "auth_failed"}

            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.db,
                        self._session_id,
                        self.password,
                        "hr.employee",
                        "write",
                        [[employee_data["id"]]],
                        employee_data,
                    ],
                },
                "id": 3,
            }
            response = self._request("POST", "/web/dataset/call_kw", json=payload)
            return {"status": "synced", "result": response.get("result")}
        except Exception as exc:
            logger.error("Failed to sync employee to Odoo: %s", exc)
            return {"status": "sync_failed", "error": str(exc)}


def _mock_employees() -> list[dict[str, Any]]:
    """Demo деректер (Odoo қол жетімді болмаған кезде)."""
    return [
        {
            "id": 1,
            "name": "Айнұр Смаилова",
            "email": "ainur@company.kz",
            "department_id": [1, "IT бөлімі"],
            "job_id": [1, "Software Engineer"],
        },
        {
            "id": 2,
            "name": "Ержан Құдайбергенов",
            "email": "erzhan@company.kz",
            "department_id": [2, "Қаржы бөлімі"],
            "job_id": [2, "Accountant"],
        },
    ]
