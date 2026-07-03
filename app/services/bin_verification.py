"""
BIN (Business Identification Number) verification service.

Calls the Kazakhstan government API (stat.gov.kz) to verify
company information during registration.

API: https://stat.gov.kz/api/legal/rest/names/bin?bin={bin}&lang=ru
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class BINVerificationResult:
    valid: bool
    company_name: str = ""
    registration_date: date | None = None
    company_status: str = ""
    legal_address: str = ""
    error: str = ""
    raw_response: dict = field(default_factory=dict)


def verify_bin(bin_number: str) -> BINVerificationResult:
    """
    Verify a Kazakhstan BIN via stat.gov.kz API.

    Returns a BINVerificationResult.
    On timeout or API down:
      - valid=False, error set — caller should allow registration but mark as unverified.
    On valid BIN:
      - valid=True, all fields populated from official API response.
    On invalid BIN:
      - valid=False, error="БИН табылмады"
    """
    if not bin_number or len(bin_number) != 12 or not bin_number.isdigit():
        return BINVerificationResult(valid=False, error="БИН 12 цифрдан тұруы керек")

    api_url = getattr(settings, "EGOV_API_URL", "https://stat.gov.kz/api/legal/rest/names/bin")
    timeout = getattr(settings, "EGOV_API_TIMEOUT", 5.0)
    url = f"{api_url}?bin={bin_number}&lang=ru"

    try:
        with httpx.Client(timeout=float(timeout)) as client:
            response = client.get(url)

        if response.status_code == 404 or response.status_code == 204:
            return BINVerificationResult(valid=False, error="БИН табылмады")

        response.raise_for_status()
        data = response.json()

        # stat.gov.kz returns a list; take first item if list, or dict directly
        if isinstance(data, list):
            if not data:
                return BINVerificationResult(valid=False, error="БИН табылмады")
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            return BINVerificationResult(valid=False, error="БИН табылмады")

        # Parse registration date
        reg_date: date | None = None
        reg_date_str = item.get("registrationDate") or item.get("reg_date") or ""
        if reg_date_str:
            try:
                reg_date = datetime.strptime(reg_date_str[:10], "%Y-%m-%d").date()
            except Exception:
                pass

        # Determine status
        status_raw = item.get("activity") or item.get("status") or item.get("statusName") or ""
        company_status = "active" if "действу" in str(status_raw).lower() or "жұмыс" in str(status_raw).lower() else str(status_raw)

        company_name = (
            item.get("nameRu")
            or item.get("name_ru")
            or item.get("name")
            or item.get("fullNameRu")
            or ""
        )
        legal_address = (
            item.get("legalAddress")
            or item.get("legal_address")
            or item.get("address")
            or ""
        )

        if not company_name:
            return BINVerificationResult(valid=False, error="БИН табылмады")

        return BINVerificationResult(
            valid=True,
            company_name=company_name,
            registration_date=reg_date,
            company_status=company_status,
            legal_address=legal_address,
            raw_response=item,
        )

    except httpx.TimeoutException:
        logger.warning("BIN verification timeout for BIN %s", bin_number)
        return BINVerificationResult(
            valid=False,
            error="API уақыты аяқталды — кейін тексеріледі",
        )
    except httpx.HTTPError as exc:
        logger.error("BIN verification HTTP error for BIN %s: %s", bin_number, exc)
        return BINVerificationResult(
            valid=False,
            error=f"API қолжетімсіз — кейін тексеріледі",
        )
    except Exception as exc:
        logger.error("Unexpected BIN verification error for BIN %s: %s", bin_number, exc)
        return BINVerificationResult(
            valid=False,
            error="Тексеру сәтсіз — кейін тексеріледі",
        )
