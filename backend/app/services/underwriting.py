"""Hybrid underwriting engine: deterministic risk rules + optional LLM narrative."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

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


def _base_rate(product_line: str) -> float:
    rates = {"auto": 0.045, "home": 0.012, "life": 0.008, "commercial": 0.025}
    return rates.get(product_line.lower(), 0.02)


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

    # Credit quality
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

    # Claims history
    if claims == 0:
        score -= 8
        reasons.append("Clean prior-claims history supports standard acceptance.")
    elif claims == 1:
        score += 8
        reasons.append("One prior claim warrants modest loading.")
    else:
        score += 8 + (claims - 1) * 10
        reasons.append(f"{claims} prior claims indicate elevated loss propensity.")

    # Age bands by product
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

    # Affordability / moral hazard proxy
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

    # Premium indication (illustrative only)
    load = 1.0 + (score / 100.0)
    if claims:
        load += 0.08 * claims
    premium = round(coverage * _base_rate(product) * load, 2)

    explanation = _maybe_llm_explanation(payload, recommendation, score, reasons, premium)
    if not explanation:
        explanation = (
            f"Deterministic underwriting engine scored this risk at {score}/100 and recommends "
            f"**{recommendation.upper()}**. Key drivers: " + " ".join(reasons) +
            f" Indicative annual premium: ${premium:,.2f}. "
            "This is decision-support only; final authority remains with the licensed underwriter."
        )

    return UnderwritingResult(recommendation, score, explanation, premium)


def _maybe_llm_explanation(
    payload: dict,
    recommendation: str,
    score: float,
    reasons: list[str],
    premium: float,
) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return ""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = {
            "task": "Write a concise underwriting rationale for insurance staff.",
            "recommendation": recommendation,
            "risk_score": score,
            "suggested_premium": premium,
            "rule_drivers": reasons,
            "application": payload,
            "tone": "professional, neutral, audit-friendly",
            "constraints": [
                "Do not invent facts not present in inputs",
                "State that AI is advisory only",
                "Keep under 180 words",
            ],
        }
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an insurance underwriting assistant that explains risk decisions clearly.",
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
            temperature=0.2,
            max_tokens=280,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""
