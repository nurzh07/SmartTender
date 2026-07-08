from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.core.security import get_current_active_user

router = APIRouter()


@router.get("/external-tenders")
async def get_external_tenders(
    category: Optional[str] = None,
    region: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Сыртқы тендерлерді алу (Goszakupki.kz, Samruk-Kazyna)
    """
    try:
        from app.services.tender_monitoring import fetch_external_tenders
        
        tenders = await fetch_external_tenders(
            category=category,
            region=region,
            min_price=min_price,
            max_price=max_price
        )
        
        return {
            "count": len(tenders),
            "tenders": tenders
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Тендерлерді алу қатесі: {str(e)}"
        )


@router.post("/watchlist")
async def add_to_watchlist(
    tender_id: str,
    source: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Тендерді бақылау тізіміне_қосу
    """
    try:
        from app.services.tender_monitoring import add_to_watchlist
        
        result = await add_to_watchlist(
            user_id=current_user.id,
            tender_id=tender_id,
            source=source
        )
        
        return {"status": "added", "watchlist_id": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Бақылау тізіміне қосу қатесі: {str(e)}"
        )


@router.get("/watchlist")
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Пайдаланушының бақылау тізімі
    """
    try:
        from app.services.tender_monitoring import get_user_watchlist
        
        watchlist = await get_user_watchlist(current_user.id)
        
        return {
            "count": len(watchlist),
            "watchlist": watchlist
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Бақылау тізімін алу қатесі: {str(e)}"
        )


@router.delete("/watchlist/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Бақылау тізімінен өшіру
    """
    try:
        from app.services.tender_monitoring import remove_from_watchlist
        
        await remove_from_watchlist(watchlist_id, current_user.id)
        
        return {"status": "removed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Бақылау тізімінен өшіру қатесі: {str(e)}"
        )


@router.get("/categories")
async def get_monitoring_categories():
    """
    Мониторинг категориялары
    """
    categories = [
        {"id": "construction", "name": "Құрылыс", "name_kk": "Құрылыс"},
        {"id": "it", "name": "IT және бағдарламалық жасақтама", "name_kk": "IT және бағдарламалық жасақтама"},
        {"id": "equipment", "name": "Жабдықтар", "name_kk": "Жабдықтар"},
        {"id": "services", "name": "Қызметтер", "name_kk": "Қызметтер"},
        {"id": "transport", "name": "Транспорт", "name_kk": "Транспорт"},
        {"id": "medical", "name": "Медициналық", "name_kk": "Медициналық"},
        {"id": "education", "name": "Білім беру", "name_kk": "Білім беру"},
        {"id": "food", "name": "Азық-түлік", "name_kk": "Азық-түлік"},
    ]
    
    return {"categories": categories}


@router.get("/regions")
async def get_monitoring_regions():
    """
    Мониторинг аймақтары
    """
    regions = [
        {"id": "almaty", "name": "Алматы қаласы", "name_kk": "Алматы қаласы"},
        {"id": "astana", "name": "Астана қаласы", "name_kk": "Астана қаласы"},
        {"id": "shymkent", "name": "Шымкент қаласы", "name_kk": "Шымкент қаласы"},
        {"id": "almaty_region", "name": "Алматы облысы", "name_kk": "Алматы облысы"},
        {"id": "astana_region", "name": "Астана облысы", "name_kk": "Астана облысы"},
        {"id": "shymkent_region", "name": "Шымкент облысы", "name_kk": "Шымкент облысы"},
        {"id": "aktobe", "name": "Ақтөбе облысы", "name_kk": "Ақтөбе облысы"},
        {"id": "atyrau", "name": "Атырау облысы", "name_kk": "Атырау облысы"},
        {"id": "karaganda", "name": "Қарағанды облысы", "name_kk": "Қарағанды облысы"},
        {"id": "kostanay", "name": "Қостанай облысы", "name_kk": "Қостанай облысы"},
    ]
    
    return {"regions": regions}
