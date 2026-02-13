from datetime import datetime, timezone
from typing import Annotated, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str


class SignoutBase(BaseModel):
    case_id: str = Field(min_length=1)
    illness_severity: str
    patient_summary: str
    action_list: list[str]
    situational_awareness: list[str]
    contingency_plans: list[str]
    receiver_synthesis: str
    free_text: str | None = None

    @field_validator("illness_severity")
    @classmethod
    def validate_illness_severity(cls, value: str) -> str:
        allowed = {"Stable", "Watcher", "Unstable"}
        if value not in allowed:
            raise ValueError("illness_severity must be one of Stable|Watcher|Unstable")
        return value

    @field_validator("action_list", "situational_awareness", "contingency_plans", mode="before")
    @classmethod
    def normalize_text_or_list(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            lines = [line.strip() for line in value.splitlines()]
            return [line for line in lines if line]
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            normalized = [item.strip() for item in value]
            return [item for item in normalized if item]
        raise ValueError("must be a list of strings or newline-separated text")


class SignoutRecord(SignoutBase):
    id: str
    created_at: datetime


class SignoutCreateResponse(BaseModel):
    signout_id: str


class SignoutMetadata(BaseModel):
    id: str
    created_at: datetime


app = FastAPI(title="signout-sim-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIGNOUT_STORE: dict[str, SignoutRecord] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/signouts", response_model=SignoutCreateResponse)
def create_signout(payload: SignoutBase) -> SignoutCreateResponse:
    signout_id = str(uuid4())
    SIGNOUT_STORE[signout_id] = SignoutRecord(
        id=signout_id,
        created_at=datetime.now(timezone.utc),
        **payload.model_dump(),
    )
    return SignoutCreateResponse(signout_id=signout_id)


@app.get("/api/signouts/{signout_id}", response_model=SignoutRecord)
def get_signout(signout_id: str) -> SignoutRecord:
    signout = SIGNOUT_STORE.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=404, detail="Signout not found")
    return signout


@app.get("/api/signouts", response_model=list[SignoutMetadata])
def list_signouts(
    case_id: Annotated[str, Query(min_length=1)],
) -> list[SignoutMetadata]:
    records = [
        SignoutMetadata(id=record.id, created_at=record.created_at)
        for record in SIGNOUT_STORE.values()
        if record.case_id == case_id
    ]
    return sorted(records, key=lambda record: record.created_at)
