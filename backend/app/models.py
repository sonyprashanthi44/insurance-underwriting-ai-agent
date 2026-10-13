from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="underwriter")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applications = relationship("PolicyApplication", back_populates="reviewer")


class PolicyApplication(Base):
    __tablename__ = "policy_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    applicant_name: Mapped[str] = mapped_column(String(255))
    applicant_age: Mapped[int] = mapped_column(Integer)
    occupation: Mapped[str] = mapped_column(String(255))
    product_line: Mapped[str] = mapped_column(String(100))  # auto | home | life | commercial
    coverage_amount: Mapped[float] = mapped_column(Float)
    annual_income: Mapped[float] = mapped_column(Float)
    credit_score: Mapped[int] = mapped_column(Integer)
    prior_claims: Mapped[int] = mapped_column(Integer, default=0)
    risk_factors: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    property_zip: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending|approved|declined|referred
    ai_recommendation: Mapped[str] = mapped_column(String(50), default="")
    ai_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    ai_explanation: Mapped[str] = mapped_column(Text, default="")
    ai_suggested_premium: Mapped[float] = mapped_column(Float, default=0.0)
    underwriter_notes: Mapped[str] = mapped_column(Text, default="")
    final_decision: Mapped[str] = mapped_column(String(50), default="")
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reviewer = relationship("User", back_populates="applications")
