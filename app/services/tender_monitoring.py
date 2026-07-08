import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User


# Goszakupki.kz API endpoints
GOSZAKUPKI_API_URL = "https://goszakupki.kz/api/v1/tenders"
SAMRUK_KAZNYA_API_URL = "https://samruk-kazyna.kz/api/v1/tenders"


async def fetch_external_tenders(
    category: Optional[str] = None,
    region: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Сыртқы тендерлерді алу (Goszakupki.kz, Samruk-Kazyna)
    """
    tenders = []
    
    # Goszakupki.kz-тен тендерлерді алу
    try:
        goszakupki_tenders = await fetch_goszakupki_tenders(
            category=category,
            region=region,
            min_price=min_price,
            max_price=max_price
        )
        tenders.extend(goszakupki_tenders)
    except Exception as e:
        print(f"Goszakupki.kz error: {e}")
    
    # Samruk-Kazyna-дан тендерлерді алу
    try:
        samruk_tenders = await fetch_samruk_tenders(
            category=category,
            region=region,
            min_price=min_price,
            max_price=max_price
        )
        tenders.extend(samruk_tenders)
    except Exception as e:
        print(f"Samruk-Kazyna error: {e}")
    
    return tenders


async def fetch_goszakupki_tenders(
    category: Optional[str] = None,
    region: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Goszakupki.kz API арқылы тендерлерді алу
    """
    params = {}
    if category:
        params["category"] = category
    if region:
        params["region"] = region
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(GOSZAKUPKI_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # API жауабын қалыптастыру
            tenders = []
            for tender in data.get("tenders", []):
                tenders.append({
                    "id": tender.get("id"),
                    "title": tender.get("title"),
                    "description": tender.get("description"),
                    "price": tender.get("price"),
                    "currency": tender.get("currency", "KZT"),
                    "category": tender.get("category"),
                    "region": tender.get("region"),
                    "deadline": tender.get("deadline"),
                    "source": "goszakupki",
                    "url": tender.get("url"),
                    "published_at": tender.get("published_at")
                })
            
            return tenders
        except httpx.HTTPError as e:
            print(f"Goszakupki.kz HTTP error: {e}")
            return []
        except Exception as e:
            print(f"Goszakupki.kz error: {e}")
            return []


async def fetch_samruk_tenders(
    category: Optional[str] = None,
    region: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Samruk-Kazyna API арқылы тендерлерді алу
    """
    params = {}
    if category:
        params["category"] = category
    if region:
        params["region"] = region
    if min_price:
        params["min_price"] = min_price
    if max_price:
        params["max_price"] = max_price
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(SAMRUK_KAZNYA_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # API жауабын қалыптастыру
            tenders = []
            for tender in data.get("tenders", []):
                tenders.append({
                    "id": tender.get("id"),
                    "title": tender.get("title"),
                    "description": tender.get("description"),
                    "price": tender.get("price"),
                    "currency": tender.get("currency", "KZT"),
                    "category": tender.get("category"),
                    "region": tender.get("region"),
                    "deadline": tender.get("deadline"),
                    "source": "samruk_kazyna",
                    "url": tender.get("url"),
                    "published_at": tender.get("published_at")
                })
            
            return tenders
        except httpx.HTTPError as e:
            print(f"Samruk-Kazyna HTTP error: {e}")
            return []
        except Exception as e:
            print(f"Samruk-Kazyna error: {e}")
            return []


async def add_to_watchlist(user_id: int, tender_id: str, source: str) -> int:
    """
    Тендерді бақылау тізіміне қосу
    """
    db = SessionLocal()
    try:
        # Бақылау тізіміндегі элементті жасау
        from app.models.monitoring import TenderWatchlist
        
        watchlist_item = TenderWatchlist(
            user_id=user_id,
            tender_id=tender_id,
            source=source,
            created_at=datetime.utcnow()
        )
        
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        
        return watchlist_item.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


async def get_user_watchlist(user_id: int) -> List[Dict[str, Any]]:
    """
    Пайдаланушының бақылау тізімі
    """
    db = SessionLocal()
    try:
        from app.models.monitoring import TenderWatchlist
        
        watchlist_items = db.query(TenderWatchlist).filter(
            TenderWatchlist.user_id == user_id
        ).all()
        
        result = []
        for item in watchlist_items:
            result.append({
                "id": item.id,
                "tender_id": item.tender_id,
                "source": item.source,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        
        return result
    except Exception as e:
        raise e
    finally:
        db.close()


async def remove_from_watchlist(watchlist_id: int, user_id: int):
    """
    Бақылау тізімінен өшіру
    """
    db = SessionLocal()
    try:
        from app.models.monitoring import TenderWatchlist
        
        watchlist_item = db.query(TenderWatchlist).filter(
            TenderWatchlist.id == watchlist_id,
            TenderWatchlist.user_id == user_id
        ).first()
        
        if watchlist_item:
            db.delete(watchlist_item)
            db.commit()
        else:
            raise ValueError("Watchlist item not found")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
