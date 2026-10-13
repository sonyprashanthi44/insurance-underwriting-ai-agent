from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ApplicationCreate(BaseModel):
    applicant_name: str
    applicant_age: int = Field(ge=18, le=100)
    occupation: str
    product_line: str
    coverage_amount: float = Field(gt=0)
    annual_income: float = Field(ge=0)
    credit_score: int = Field(ge=300, le=850)
    prior_claims: int = Field(ge=0, default=0)
    risk_factors: str = ""
    property_zip: str = ""


class ApplicationUpdateDecision(BaseModel):
    final_decision: str  # approved | declined | referred
    underwriter_notes: str = ""


class ApplicationOut(BaseModel):
    id: int
    application_number: str
    applicant_name: str
    applicant_age: int
    occupation: str
    product_line: str
    coverage_amount: float
    annual_income: float
    credit_score: int
    prior_claims: int
    risk_factors: str
    property_zip: str
    status: str
    ai_recommendation: str
    ai_risk_score: float
    ai_explanation: str
    ai_suggested_premium: float
    underwriter_notes: str
    final_decision: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total: int
    pending: int
    approved: int
    declined: int
    referred: int
    avg_risk_score: float
