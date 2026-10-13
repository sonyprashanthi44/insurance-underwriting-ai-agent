from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import hash_password
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import PolicyApplication, User
from app.routers import applications, auth
from app.services.underwriting import score_application

settings = get_settings()

app = FastAPI(
    title="Insurance Underwriting AI Assistant",
    description="Decision-support for policy application review — AI recommends, underwriters decide.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(applications.router)

SEED = [
    {
        "applicant_name": "Aisha Rahman",
        "applicant_age": 34,
        "occupation": "Software Engineer",
        "product_line": "auto",
        "coverage_amount": 50000,
        "annual_income": 120000,
        "credit_score": 780,
        "prior_claims": 0,
        "risk_factors": "",
        "property_zip": "07302",
    },
    {
        "applicant_name": "Marcus Cole",
        "applicant_age": 22,
        "occupation": "Commercial Driver",
        "product_line": "auto",
        "coverage_amount": 100000,
        "annual_income": 48000,
        "credit_score": 610,
        "prior_claims": 2,
        "risk_factors": "DUI, high crime area",
        "property_zip": "48226",
    },
    {
        "applicant_name": "Elena Vargas",
        "applicant_age": 47,
        "occupation": "Teacher",
        "product_line": "home",
        "coverage_amount": 450000,
        "annual_income": 78000,
        "credit_score": 720,
        "prior_claims": 1,
        "risk_factors": "flood zone, roof > 20 years",
        "property_zip": "33139",
    },
    {
        "applicant_name": "James Okonkwo",
        "applicant_age": 58,
        "occupation": "Accountant",
        "product_line": "life",
        "coverage_amount": 1000000,
        "annual_income": 95000,
        "credit_score": 745,
        "prior_claims": 0,
        "risk_factors": "smoking",
        "property_zip": "10001",
    },
    {
        "applicant_name": "Priya Nair",
        "applicant_age": 41,
        "occupation": "Business Owner",
        "product_line": "commercial",
        "coverage_amount": 2500000,
        "annual_income": 310000,
        "credit_score": 700,
        "prior_claims": 1,
        "risk_factors": "coastal exposure",
        "property_zip": "92101",
    },
]


def seed_db() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.demo_user_email).first()
        if not user:
            user = User(
                email=settings.demo_user_email,
                full_name="Demo Underwriter",
                hashed_password=hash_password(settings.demo_user_password),
                role="underwriter",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if db.query(PolicyApplication).count() == 0:
            for i, raw in enumerate(SEED, start=1):
                result = score_application(raw)
                row = PolicyApplication(
                    application_number=f"UW-SEED-{i:03d}",
                    **raw,
                    status="pending",
                    ai_recommendation=result.recommendation,
                    ai_risk_score=result.risk_score,
                    ai_explanation=result.explanation,
                    ai_suggested_premium=result.suggested_premium,
                    reviewer_id=user.id,
                )
                db.add(row)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "underwriting-ai-assistant"}


# Serve built React UI when present (single-service deploy)
STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str = ""):
        index = STATIC_DIR / "index.html"
        candidate = STATIC_DIR / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
