from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.supplier_rating import SupplierRating, SupplierPortfolio, SupplierCertification
from app.core.security import get_current_active_user

router = APIRouter()


# ── Pydantic Schemas ───────────────────────────────────────────
class RatingCreate(BaseModel):
    tender_id: int
    supplier_id: int
    quality_score: float
    delivery_score: float
    communication_score: float
    price_score: float
    review: Optional[str] = None


class RatingResponse(BaseModel):
    id: int
    supplier_id: int
    tender_id: int
    buyer_id: int
    quality_score: float
    delivery_score: float
    communication_score: float
    price_score: float
    avg_score: float
    review: Optional[str]
    is_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True


class PortfolioCreate(BaseModel):
    project_name: str
    project_description: Optional[str] = None
    project_value: Optional[float] = None
    completion_date: Optional[str] = None
    client_name: Optional[str] = None
    client_contact: Optional[str] = None
    documents: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: int
    supplier_id: int
    project_name: str
    project_description: Optional[str]
    project_value: Optional[float]
    completion_date: Optional[str]
    client_name: Optional[str]
    client_contact: Optional[str]
    documents: Optional[str]
    is_verified: bool
    is_featured: bool
    created_at: str
    
    class Config:
        from_attributes = True


class CertificationCreate(BaseModel):
    certification_name: str
    issuing_organization: str
    certificate_number: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    document_url: Optional[str] = None


class CertificationResponse(BaseModel):
    id: int
    supplier_id: int
    certification_name: str
    issuing_organization: str
    certificate_number: Optional[str]
    issue_date: Optional[str]
    expiry_date: Optional[str]
    document_url: Optional[str]
    is_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True


# ── Rating Endpoints ───────────────────────────────────────────
@router.post("/ratings", response_model=RatingResponse)
async def create_rating(
    rating: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Жеткізушіге рейтинг қою
    """
    # Buyer тек қоя алады
    if current_user.role.value not in ["buyer", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек buyer рейтинг қоя алады"
        )
    
    # Орташа бағаны есептеу
    avg_score = (rating.quality_score + rating.delivery_score + 
                 rating.communication_score + rating.price_score) / 4
    
    new_rating = SupplierRating(
        supplier_id=rating.supplier_id,
        tender_id=rating.tender_id,
        buyer_id=current_user.id,
        quality_score=rating.quality_score,
        delivery_score=rating.delivery_score,
        communication_score=rating.communication_score,
        price_score=rating.price_score,
        avg_score=avg_score,
        review=rating.review
    )
    
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    
    return new_rating


@router.get("/ratings/supplier/{supplier_id}", response_model=List[RatingResponse])
async def get_supplier_ratings(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Жеткізушінің рейтингтері
    """
    ratings = db.query(SupplierRating).filter(
        SupplierRating.supplier_id == supplier_id
    ).all()
    
    return ratings


@router.get("/ratings/tender/{tender_id}", response_model=List[RatingResponse])
async def get_tender_ratings(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Тендерге берілген рейтингтер
    """
    ratings = db.query(SupplierRating).filter(
        SupplierRating.tender_id == tender_id
    ).all()
    
    return ratings


@router.get("/ratings/supplier/{supplier_id}/average")
async def get_supplier_average_rating(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Жеткізушінің орташа рейтингі
    """
    ratings = db.query(SupplierRating).filter(
        SupplierRating.supplier_id == supplier_id
    ).all()
    
    if not ratings:
        return {
            "supplier_id": supplier_id,
            "average_rating": 0,
            "total_ratings": 0,
            "quality_avg": 0,
            "delivery_avg": 0,
            "communication_avg": 0,
            "price_avg": 0
        }
    
    total = len(ratings)
    avg = sum(r.avg_score for r in ratings) / total
    quality_avg = sum(r.quality_score for r in ratings) / total
    delivery_avg = sum(r.delivery_score for r in ratings) / total
    communication_avg = sum(r.communication_score for r in ratings) / total
    price_avg = sum(r.price_score for r in ratings) / total
    
    return {
        "supplier_id": supplier_id,
        "average_rating": round(avg, 2),
        "total_ratings": total,
        "quality_avg": round(quality_avg, 2),
        "delivery_avg": round(delivery_avg, 2),
        "communication_avg": round(communication_avg, 2),
        "price_avg": round(price_avg, 2)
    }


# ── Portfolio Endpoints ────────────────────────────────────────
@router.post("/portfolio", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Портфолио қосу
    """
    # Supplier тек қоса алады
    if current_user.role.value not in ["supplier", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек supplier портфолио қоса алады"
        )
    
    new_portfolio = SupplierPortfolio(
        supplier_id=current_user.id,
        project_name=portfolio.project_name,
        project_description=portfolio.project_description,
        project_value=portfolio.project_value,
        completion_date=portfolio.completion_date,
        client_name=portfolio.client_name,
        client_contact=portfolio.client_contact,
        documents=portfolio.documents
    )
    
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    
    return new_portfolio


@router.get("/portfolio/supplier/{supplier_id}", response_model=List[PortfolioResponse])
async def get_supplier_portfolio(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Жеткізушінің портфолиосы
    """
    portfolios = db.query(SupplierPortfolio).filter(
        SupplierPortfolio.supplier_id == supplier_id
    ).all()
    
    return portfolios


@router.get("/portfolio/my", response_model=List[PortfolioResponse])
async def get_my_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Менің портфолиом
    """
    if current_user.role.value not in ["supplier", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек supplier портфолио көре алады"
        )
    
    portfolios = db.query(SupplierPortfolio).filter(
        SupplierPortfolio.supplier_id == current_user.id
    ).all()
    
    return portfolios


@router.put("/portfolio/{portfolio_id}")
async def update_portfolio(
    portfolio_id: int,
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Портфолио жаңарту
    """
    portfolio_item = db.query(SupplierPortfolio).filter(
        SupplierPortfolio.id == portfolio_id,
        SupplierPortfolio.supplier_id == current_user.id
    ).first()
    
    if not portfolio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфолио табылмады"
        )
    
    portfolio_item.project_name = portfolio.project_name
    portfolio_item.project_description = portfolio.project_description
    portfolio_item.project_value = portfolio.project_value
    portfolio_item.completion_date = portfolio.completion_date
    portfolio_item.client_name = portfolio.client_name
    portfolio_item.client_contact = portfolio.client_contact
    portfolio_item.documents = portfolio.documents
    
    db.commit()
    db.refresh(portfolio_item)
    
    return portfolio_item


@router.delete("/portfolio/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Портфолио өшіру
    """
    portfolio_item = db.query(SupplierPortfolio).filter(
        SupplierPortfolio.id == portfolio_id,
        SupplierPortfolio.supplier_id == current_user.id
    ).first()
    
    if not portfolio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Портфолио табылмады"
        )
    
    db.delete(portfolio_item)
    db.commit()
    
    return {"status": "deleted"}


# ── Certification Endpoints ────────────────────────────────────
@router.post("/certifications", response_model=CertificationResponse)
async def create_certification(
    certification: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Сертификат қосу
    """
    # Supplier тек қоса алады
    if current_user.role.value not in ["supplier", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек supplier сертификат қоса алады"
        )
    
    new_certification = SupplierCertification(
        supplier_id=current_user.id,
        certification_name=certification.certification_name,
        issuing_organization=certification.issuing_organization,
        certificate_number=certification.certificate_number,
        issue_date=certification.issue_date,
        expiry_date=certification.expiry_date,
        document_url=certification.document_url
    )
    
    db.add(new_certification)
    db.commit()
    db.refresh(new_certification)
    
    return new_certification


@router.get("/certifications/supplier/{supplier_id}", response_model=List[CertificationResponse])
async def get_supplier_certifications(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Жеткізушінің сертификаттары
    """
    certifications = db.query(SupplierCertification).filter(
        SupplierCertification.supplier_id == supplier_id
    ).all()
    
    return certifications


@router.get("/certifications/my", response_model=List[CertificationResponse])
async def get_my_certifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Менің сертификаттарым
    """
    if current_user.role.value not in ["supplier", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Тек supplier сертификаттар көре алады"
        )
    
    certifications = db.query(SupplierCertification).filter(
        SupplierCertification.supplier_id == current_user.id
    ).all()
    
    return certifications


@router.delete("/certifications/{certification_id}")
async def delete_certification(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Сертификат өшіру
    """
    certification = db.query(SupplierCertification).filter(
        SupplierCertification.id == certification_id,
        SupplierCertification.supplier_id == current_user.id
    ).first()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сертификат табылмады"
        )
    
    db.delete(certification)
    db.commit()
    
    return {"status": "deleted"}
