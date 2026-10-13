"""Hybrid underwriting: deterministic rules + optional Gemini narrative (token-light)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import httpx

from app.config import get_settings

HIGH_RISK_OCCUPATIONS = {
    "construction worker",
    "roofer",
    "miner",
    "pilot",
    "stunt performer",
    "logger",
    "commercial driver",
}

HAZARDOUS_FACTORS = {
    "smoking",
    "flood zone",
    "high crime area",
    "prior bankruptcy",
    "dui",
    "uninsured motorist history",
    "roof > 20 years",
    "coastal exposure",
}


@dataclass
class UnderwritingResult:
    recommendation: str
    risk_score: float
    explanation: str
    suggested_premium: float
    suggestions: list[str] = field(default_factory=list)


def _base_rate(product_line: str) -> float:
    rates = {"auto": 0.045, "home": 0.012, "life": 0.008, "commercial": 0.025}
    return rates.get(product_line.lower(), 0.02)


def _rule_suggestions(
    recommendation: str,
    score: float,
    product: str,
    credit: int,
    claims: int,
    ratio: float | None,
    matched_hazards: set[str],
    occupation: str,
) -> list[str]:
    tips: list[str] = []
    if recommendation == "approve":
        tips.append("Issue at standard terms; document clean credit/claims drivers in file notes.")
        if score < 30:
            tips.append("Eligible for preferred-tier pricing if carrier guidelines allow.")
    elif recommendation == "refer":
        tips.append("Route to senior UW; request supporting docs before binding.")
        tips.append("Consider conditional offer (higher deductible, exclusion, or surcharge).")
    else:
        tips.append("Decline or counter with reduced limits only if appetite allows.")
        tips.append("Log adverse action reasons for audit / fair-lending review.")

    if credit < 680:
        tips.append("Verify credit attributes and recent score changes before finalizing.")
    if claims >= 2:
        tips.append("Pull full loss runs (3-5 years) and note cause codes.")
    if ratio is not None and ratio > 8:
        tips.append("Validate coverage need vs. income/assets; consider lower limits.")
    if matched_hazards:
        tips.append("Mitigation checklist: " + ", ".join(sorted(matched_hazards)) + ".")
    if occupation in HIGH_RISK_OCCUPATIONS:
        tips.append("Confirm job duties and safety controls for hazard-class occupation.")
    if product == "home" and "flood zone" in matched_hazards:
        tips.append("Require flood questionnaire / elevation certificate if writing property.")
    if product == "auto" and "dui" in matched_hazards:
        tips.append("Confirm DUI date, completion of programs, and SR-22 needs.")
    if product == "life" and "smoking" in matched_hazards:
        tips.append("Order cotinine test and apply smoker rates if confirmed.")

    seen: set[str] = set()
    out: list[str] = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= 6:
            break
    return out


def score_application(payload: dict) -> UnderwritingResult:
    score = 35.0
    reasons: list[str] = []

    age = int(payload["applicant_age"])
    credit = int(payload["credit_score"])
    claims = int(payload.get("prior_claims") or 0)
    coverage = float(payload["coverage_amount"])
    income = float(payload["annual_income"])
    occupation = (payload.get("occupation") or "").strip().lower()
    product = (payload.get("product_line") or "auto").lower()
    factors_raw = payload.get("risk_factors") or ""
    factors = {f.strip().lower() for f in re.split(r"[,;|]", factors_raw) if f.strip()}

    if credit >= 750:
        score -= 12
        reasons.append(f"Strong credit score ({credit}) reduces expected loss frequency.")
    elif credit >= 680:
        score -= 4
        reasons.append(f"Acceptable credit score ({credit}).")
    elif credit >= 620:
        score += 10
        reasons.append(f"Borderline credit score ({credit}) increases non-pay and claim risk.")
    else:
        score += 22
        reasons.append(f"Low credit score ({credit}) is a material underwriting concern.")

    if claims == 0:
        score -= 8
        reasons.append("Clean prior-claims history supports standard acceptance.")
    elif claims == 1:
        score += 8
        reasons.append("One prior claim warrants modest loading.")
    else:
        score += 8 + (claims - 1) * 10
        reasons.append(f"{claims} prior claims indicate elevated loss propensity.")

    if product == "auto":
        if age < 25:
            score += 15
            reasons.append("Youthful operator age increases auto frequency risk.")
        elif age > 70:
            score += 8
            reasons.append("Senior operator age may elevate severity risk.")
        else:
            score -= 5
    elif product == "life":
        if age > 60:
            score += 12
            reasons.append("Higher attained age increases mortality risk.")
        elif age < 40:
            score -= 6
            reasons.append("Favorable age band for life mortality assumptions.")

    ratio: float | None = None
    if income > 0:
        ratio = coverage / income
        if ratio > 15:
            score += 18
            reasons.append(f"Coverage-to-income ratio ({ratio:.1f}x) is aggressive.")
        elif ratio > 8:
            score += 8
            reasons.append(f"Coverage-to-income ratio ({ratio:.1f}x) is elevated.")
        else:
            score -= 4
            reasons.append("Coverage request is reasonably aligned with income.")

    if occupation in HIGH_RISK_OCCUPATIONS:
        score += 14
        reasons.append(f"Occupation '{occupation}' maps to higher hazard class.")

    matched_hazards = factors & HAZARDOUS_FACTORS
    if matched_hazards:
        score += 6 * len(matched_hazards)
        reasons.append("Hazard flags: " + ", ".join(sorted(matched_hazards)) + ".")

    score = max(0.0, min(100.0, round(score, 1)))

    if score < 40:
        recommendation = "approve"
    elif score < 65:
        recommendation = "refer"
    else:
        recommendation = "decline"

    load = 1.0 + (score / 100.0)
    if claims:
        load += 0.08 * claims
    premium = round(coverage * _base_rate(product) * load, 2)

    suggestions = _rule_suggestions(
        recommendation, score, product, credit, claims, ratio, matched_hazards, occupation
    )

    explanation = _maybe_gemini_narrative(payload, recommendation, score, reasons, premium, suggestions)
    if not explanation:
        explanation = (
            f"Rule engine scored this risk at {score}/100 and recommends "
            f"**{recommendation.upper()}**. Key drivers: " + " ".join(reasons) +
            f" Indicative annual premium: ${premium:,.2f}. "
            "Advisory only — final authority remains with the licensed underwriter."
        )

    return UnderwritingResult(recommendation, score, explanation, premium, suggestions)


def _maybe_gemini_narrative(
    payload: dict,
    recommendation: str,
    score: float,
    reasons: list[str],
    premium: float,
    suggestions: list[str],
) -> str:
    """Short Gemini rewrite; fails soft to empty string (rules still apply)."""
    settings = get_settings()
    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        return ""

    user_blob = {
        "rec": recommendation,
        "score": score,
        "prem": premium,
        "drivers": reasons[:6],
        "next": suggestions[:4],
        "app": {
            "age": payload.get("applicant_age"),
            "occ": payload.get("occupation"),
            "line": payload.get("product_line"),
            "cov": payload.get("coverage_amount"),
            "inc": payload.get("annual_income"),
            "credit": payload.get("credit_score"),
            "claims": payload.get("prior_claims"),
            "flags": payload.get("risk_factors") or "",
            "zip": payload.get("property_zip") or "",
        },
    }
    prompt = (
        "Insurance UW aide. Rewrite a tight rationale (<=120 words) for staff. "
        "Use only given facts. Neutral audit tone. End: AI is advisory only. "
        f"DATA:{json.dumps(user_blob, separators=(',', ':'))}"
    )

    model = settings.gemini_model or "gemini-2.0-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 180,
        },
    }
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, params={"key": api_key}, json=body)
            resp.raise_for_status()
            data = resp.json()
        parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return text
    except Exception:
        return ""
