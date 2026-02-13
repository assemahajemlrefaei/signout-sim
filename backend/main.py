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
    action_list: list[str] | str = Field(default_factory=list)
    situational_awareness: list[str] | str = Field(default_factory=list)
    contingency_plans: list[str] | str = Field(default_factory=list)
    receiver_synthesis: str = Field(min_length=1)
    free_text: str | None = None

    @field_validator("action_list", "situational_awareness", "contingency_plans", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
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
        raise TypeError("Value must be None, a string, or list of strings")


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


SIGNOUTS: dict[str, SignoutRecord] = {}

app = FastAPI(title="signout-sim-backend")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/signouts", response_model=SignoutRecord, status_code=status.HTTP_201_CREATED)
def create_signout(payload: SignoutCreate) -> SignoutRecord:
    signout_id = str(uuid4())
    record = SignoutRecord(
        signout_id=signout_id,
        created_at=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    SIGNOUTS[signout_id] = record
    return record


@app.get("/api/signouts", response_model=list[SignoutRecord])
def list_signouts(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    case_id: str | None = Query(None),
) -> list[SignoutRecord]:
    signouts = sorted(SIGNOUTS.values(), key=lambda record: record.created_at)
    if case_id is not None:
        signouts = [record for record in signouts if record.case_id == case_id]
    return signouts[offset : offset + limit]


@app.get("/api/signouts/{signout_id}", response_model=SignoutRecord)
def get_signout(signout_id: str) -> SignoutRecord:
    record = SIGNOUTS.get(signout_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return record


@app.post("/api/signouts/{signout_id}/score", response_model=RubricScore)
def score_signout(signout_id: str) -> RubricScore:
    record = SIGNOUTS.get(signout_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")

    summary_len = len(record.patient_summary.strip())
    synthesis_len = len(record.receiver_synthesis.strip())

    def score_len(items: list[str]) -> int:
        if len(items) >= 2:
            return 2
        if len(items) == 1:
            return 1
        return 0

    subscores = {
        "illness_severity": 2,
        "patient_summary": 2 if summary_len >= 80 else 1 if summary_len >= 20 else 0,
        "action_list": score_len(record.action_list),
        "situational_awareness": score_len(record.situational_awareness),
        "contingency_plans": score_len(record.contingency_plans),
        "receiver_synthesis": 2 if synthesis_len >= 30 else 1 if synthesis_len >= 10 else 0,
    }
    total_score = sum(subscores.values())

    strengths = [domain for domain, score in subscores.items() if score == 2]
    improvements = [domain for domain, score in subscores.items() if score < 2]

    missing_critical: list[str] = []
    if summary_len < 20:
        missing_critical.append("patient_summary")
    if not record.action_list:
        missing_critical.append("action_list")
    if not record.contingency_plans:
        missing_critical.append("contingency_plans")
    if synthesis_len < 10:
        missing_critical.append("receiver_synthesis")

    return RubricScore(
        strengths=strengths,
        improvements=improvements,
        missing_critical=missing_critical,
        subscores=subscores,
        total_score=total_score,
        rubric_version="v0.1",
    )
