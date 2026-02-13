from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str


IllnessSeverity = Literal["Stable", "Watcher", "Unstable"]


class SignoutCreate(BaseModel):
    case_id: str = Field(min_length=1)
    illness_severity: IllnessSeverity
    patient_summary: str = Field(min_length=1)
    action_list: list[str] | str
    situational_awareness: list[str] | str
    contingency_plans: list[str] | str
    receiver_synthesis: str = Field(min_length=1)
    free_text: str | None = None

    @staticmethod
    def _normalize_list_field(value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]

        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                if not isinstance(item, str):
                    raise TypeError("List items must be strings")
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
            return normalized

        raise TypeError("Value must be a string or list of strings")

    @field_validator("action_list", "situational_awareness", "contingency_plans", mode="before")
    @classmethod
    def normalize_ipass_list_fields(cls, value: list[str] | str) -> list[str]:
        return cls._normalize_list_field(value)


class SignoutRecord(SignoutCreate):
    signout_id: str
    created_at: datetime


class RubricScore(BaseModel):
    strengths: list[str]
    improvements: list[str]
    missing_critical: list[str]
    subscores: dict[str, int]
    total_score: int
    rubric_version: str


app = FastAPI(title="signout-sim-backend")

SIGNOUTS: dict[str, SignoutRecord] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/signouts", response_model=SignoutRecord, status_code=status.HTTP_201_CREATED)
def create_signout(payload: SignoutCreate) -> SignoutRecord:
    signout_id = str(uuid4())
    signout = SignoutRecord(
        signout_id=signout_id,
        created_at=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    SIGNOUTS[signout_id] = signout
    return signout


@app.get("/api/signouts", response_model=list[SignoutRecord])
def list_signouts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    case_id: str | None = Query(default=None),
) -> list[SignoutRecord]:
    signouts = sorted(SIGNOUTS.values(), key=lambda item: item.created_at)
    if case_id is not None:
        signouts = [signout for signout in signouts if signout.case_id == case_id]
    return signouts[offset : offset + limit]


@app.get("/api/signouts/{signout_id}", response_model=SignoutRecord)
def get_signout(signout_id: str) -> SignoutRecord:
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return signout


@app.post("/api/signouts/{signout_id}/score", response_model=RubricScore)
def score_signout(signout_id: str) -> RubricScore:
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")

    severity_score = 2 if signout.illness_severity in {"Watcher", "Unstable"} else 1
    summary_len = len(signout.patient_summary.strip())
    summary_score = 2 if summary_len >= 80 else 1 if summary_len >= 20 else 0
    action_score = min(2, len(signout.action_list))
    awareness_score = min(2, len(signout.situational_awareness))
    contingency_score = min(2, len(signout.contingency_plans))
    synthesis_score = 2 if len(signout.receiver_synthesis.strip()) >= 15 else 1

    subscores = {
        "illness_severity": severity_score,
        "patient_summary": summary_score,
        "action_list": action_score,
        "situational_awareness": awareness_score,
        "contingency_plans": contingency_score,
        "receiver_synthesis": synthesis_score,
    }
    total_score = sum(subscores.values())

    missing_critical: list[str] = []
    if not signout.action_list:
        missing_critical.append("action_list")
    if not signout.contingency_plans:
        missing_critical.append("contingency_plans")

    strengths = [key for key, value in subscores.items() if value >= 2]
    improvements = [key for key, value in subscores.items() if value < 2]

    return RubricScore(
        strengths=strengths,
        improvements=improvements,
        missing_critical=missing_critical,
        subscores=subscores,
        total_score=total_score,
        rubric_version="v0.1",
    )
