from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import PolicyApplication, User
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdateDecision,
    DashboardStats,
)
from app.services.underwriting import score_application

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(PolicyApplication).all()
    total = len(rows)
    def count(status: str) -> int:
        return sum(1 for r in rows if r.status == status)

    avg = round(sum(r.ai_risk_score for r in rows) / total, 2) if total else 0.0
    return DashboardStats(
        total=total,
        pending=count("pending"),
        approved=count("approved"),
        declined=count("declined"),
        referred=count("referred"),
        avg_risk_score=avg,
    )


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = Query(default=None),
    product_line: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(PolicyApplication).order_by(PolicyApplication.created_at.desc())
    if status:
        q = q.filter(PolicyApplication.status == status)
    if product_line:
        q = q.filter(PolicyApplication.product_line == product_line)
    return q.all()


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    app = db.query(PolicyApplication).filter(PolicyApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = body.model_dump()
    result = score_application(payload)
    app_no = f"UW-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    row = PolicyApplication(
        application_number=app_no,
        **payload,
        status="pending",
        ai_recommendation=result.recommendation,
        ai_risk_score=result.risk_score,
        ai_explanation=result.explanation,
        ai_suggested_premium=result.suggested_premium,
        reviewer_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{app_id}/rescore", response_model=ApplicationOut)
def rescore(app_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    app = db.query(PolicyApplication).filter(PolicyApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    payload = {
        "applicant_name": app.applicant_name,
        "applicant_age": app.applicant_age,
        "occupation": app.occupation,
        "product_line": app.product_line,
        "coverage_amount": app.coverage_amount,
        "annual_income": app.annual_income,
        "credit_score": app.credit_score,
        "prior_claims": app.prior_claims,
        "risk_factors": app.risk_factors,
        "property_zip": app.property_zip,
    }
    result = score_application(payload)
    app.ai_recommendation = result.recommendation
    app.ai_risk_score = result.risk_score
    app.ai_explanation = result.explanation
    app.ai_suggested_premium = result.suggested_premium
    db.commit()
    db.refresh(app)
    return app


@router.patch("/{app_id}/decision", response_model=ApplicationOut)
def decide(
    app_id: int,
    body: ApplicationUpdateDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed = {"approved", "declined", "referred"}
    if body.final_decision not in allowed:
        raise HTTPException(status_code=400, detail=f"final_decision must be one of {sorted(allowed)}")

    app = db.query(PolicyApplication).filter(PolicyApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.final_decision = body.final_decision
    app.status = body.final_decision
    app.underwriter_notes = body.underwriter_notes
    app.reviewer_id = current_user.id
    db.commit()
    db.refresh(app)
    return app
