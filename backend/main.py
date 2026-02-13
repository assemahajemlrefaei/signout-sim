from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str


class SignoutCreate(BaseModel):
    case_id: str
    illness_severity: str
    patient_summary: str
    action_list: list[str]
    situational_awareness: list[str]
    contingency_plans: list[str]
    receiver_synthesis: str
    free_text: str | None = None

    @field_validator("action_list", "situational_awareness", "contingency_plans", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.splitlines() if item.strip()]
        if isinstance(value, list):
            return [item.strip() for item in value if isinstance(item, str) and item.strip()]
        raise TypeError("Expected a list of strings or newline-separated string")


class SignoutRecord(SignoutCreate):
    signout_id: str
    created_at: datetime


class ScoreResponse(BaseModel):
    signout_id: str
    score: float = Field(ge=0, le=1)


app = FastAPI(title="signout-sim-backend")

SIGNOUTS: dict[str, SignoutRecord] = {}


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
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[SignoutRecord]:
    signouts = list(SIGNOUTS.values())
    return signouts[offset : offset + limit]


@app.get("/api/signouts/{signout_id}", response_model=SignoutRecord)
def get_signout(
    signout_id: str,
    view: Literal["author", "reviewer"] = Query(default="reviewer"),
) -> SignoutRecord:
    _ = view
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return signout


@app.post("/api/signouts/{signout_id}/score", response_model=ScoreResponse)
def score_signout(signout_id: str) -> ScoreResponse:
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")

    max_points = 6
    points = sum(
        [
            bool(signout.patient_summary.strip()),
            bool(signout.action_list),
            bool(signout.situational_awareness),
            bool(signout.contingency_plans),
            bool(signout.receiver_synthesis.strip()),
            bool((signout.free_text or "").strip()),
        ]
    )
    return ScoreResponse(signout_id=signout_id, score=round(points / max_points, 2))


@app.delete("/api/signouts/{signout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signout(signout_id: str) -> Response:
    signout = SIGNOUTS.pop(signout_id, None)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
