from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


IllnessSeverity = Literal["Stable", "Watcher", "Unstable"]


class SignoutBase(BaseModel):
    case_id: str
    illness_severity: IllnessSeverity
    patient_summary: str
    action_list: list[str] = Field(default_factory=list)
    situational_awareness: list[str] = Field(default_factory=list)
    contingency_plans: list[str] = Field(default_factory=list)
    receiver_synthesis: str
    free_text: str | None = None


class SignoutCreate(BaseModel):
    case_id: str
    illness_severity: IllnessSeverity
    patient_summary: str
    action_list: list[str] | str = Field(default_factory=list)
    situational_awareness: list[str] | str = Field(default_factory=list)
    contingency_plans: list[str] | str = Field(default_factory=list)
    receiver_synthesis: str
    free_text: str | None = None


class SignoutUpdate(BaseModel):
    case_id: str | None = None
    illness_severity: IllnessSeverity | None = None
    patient_summary: str | None = None
    action_list: list[str] | str | None = None
    situational_awareness: list[str] | str | None = None
    contingency_plans: list[str] | str | None = None
    receiver_synthesis: str | None = None
    free_text: str | None = None


class Signout(SignoutBase):
    signout_id: str


class RubricScore(BaseModel):
    strengths: list[str]
    improvements: list[str]
    missing_critical: list[str]
    subscores: dict[str, int]
    total_score: int
    rubric_version: str


app = FastAPI(title="signout-sim-backend")

SIGNOUTS: dict[str, Signout] = {}

TIME_THRESHOLD_KEYWORDS = ["if", "call", "worsening", "sbp<", "o2", "temp", "hr", "bp"]
DX_KEYWORDS = ["dx", "diagnosis", "pna", "pneumonia", "sepsis", "chf", "copd", "uti"]
STATUS_KEYWORDS = ["stable", "improving", "worsening", "critical", "unchanged", "watcher"]
TREATMENT_KEYWORDS = ["started", "continue", "iv", "abx", "antibiotic", "drip", "oxygen"]
RECEIVER_PLAN_KEYWORDS = ["i will", "i'll", "monitor", "check", "reassess", "call"]


def _has_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _normalize_text_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [item.strip() for item in value if item and item.strip()]


def _normalized_signout_data(payload: SignoutCreate | SignoutUpdate) -> dict:
    data = payload.model_dump(exclude_unset=True)
    if "action_list" in data:
        data["action_list"] = _normalize_text_list(data["action_list"])
    if "situational_awareness" in data:
        data["situational_awareness"] = _normalize_text_list(data["situational_awareness"])
    if "contingency_plans" in data:
        data["contingency_plans"] = _normalize_text_list(data["contingency_plans"])
    return data


def _score_list_domain(
    items: list[str],
    domain_label: str,
    strengths: list[str],
    improvements: list[str],
    missing_critical: list[str],
) -> int:
    score = 0
    if not items:
        improvements.append(f"Add {domain_label} items to make expectations explicit.")
        missing_critical.append(f"{domain_label} is empty")
        return score

    score += 1
    if len(items) >= 2:
        score += 1
        strengths.append(f"{domain_label} includes multiple concrete items.")
    else:
        improvements.append(f"Add at least 2 {domain_label} items for better coverage.")

    if _has_keyword(" ".join(items), TIME_THRESHOLD_KEYWORDS):
        score += 1
        strengths.append(f"{domain_label} includes a trigger/threshold cue.")
    else:
        improvements.append(f"Add a trigger or threshold in {domain_label} (e.g., if/HR/BP/call).")

    return score


def score_signout(signout: Signout) -> RubricScore:
    strengths: list[str] = []
    improvements: list[str] = []
    missing_critical: list[str] = []
    subscores: dict[str, int] = {
        "illness_severity": 0,
        "patient_summary": 0,
        "action_list": 0,
        "situational_awareness": 0,
        "contingency_plans": 0,
        "receiver_synthesis": 0,
    }

    if signout.illness_severity in ("Stable", "Watcher", "Unstable"):
        subscores["illness_severity"] = 2
        strengths.append("Illness severity is clearly classified.")

    summary_text = signout.patient_summary.strip()
    if summary_text:
        summary_score = 1
        if _has_keyword(summary_text, DX_KEYWORDS):
            summary_score += 1
        else:
            improvements.append("Patient summary should include diagnosis.")
        if _has_keyword(summary_text, STATUS_KEYWORDS):
            summary_score += 1
        else:
            improvements.append("Patient summary should include current clinical status.")
        if _has_keyword(summary_text, TREATMENT_KEYWORDS):
            summary_score += 1
        else:
            improvements.append("Patient summary should include current treatment.")
        if summary_score >= 3:
            strengths.append("Patient summary captures key clinical framing.")
        subscores["patient_summary"] = summary_score
    else:
        improvements.append("Add a patient summary with diagnosis, status, and treatment.")
        missing_critical.append("patient_summary is missing")

    subscores["action_list"] = _score_list_domain(
        signout.action_list,
        "action_list",
        strengths,
        improvements,
        missing_critical,
    )
    subscores["situational_awareness"] = _score_list_domain(
        signout.situational_awareness,
        "situational_awareness",
        strengths,
        improvements,
        missing_critical,
    )
    subscores["contingency_plans"] = _score_list_domain(
        signout.contingency_plans,
        "contingency_plans",
        strengths,
        improvements,
        missing_critical,
    )

    receiver_text = signout.receiver_synthesis.strip()
    if receiver_text:
        receiver_score = 1
        if _has_keyword(receiver_text, RECEIVER_PLAN_KEYWORDS):
            receiver_score += 2
            strengths.append("Receiver synthesis reflects active closed-loop planning.")
        else:
            improvements.append("Receiver synthesis should include explicit plan/acknowledgement.")
        subscores["receiver_synthesis"] = receiver_score
    else:
        improvements.append("Add receiver synthesis (e.g., I will monitor/reassess/call).")
        missing_critical.append("receiver_synthesis is missing")

    return RubricScore(
        strengths=strengths,
        improvements=improvements,
        missing_critical=missing_critical,
        subscores=subscores,
        total_score=sum(subscores.values()),
        rubric_version="v0.1",
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/signouts", response_model=Signout, status_code=status.HTTP_201_CREATED)
def create_signout(payload: SignoutCreate) -> Signout:
    normalized_data = _normalized_signout_data(payload)
    signout = Signout(signout_id=str(uuid4()), **normalized_data)
    SIGNOUTS[signout.signout_id] = signout
    return signout


@app.get("/api/signouts", response_model=list[Signout])
def list_signouts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[Signout]:
    signouts = list(SIGNOUTS.values())
    return signouts[offset : offset + limit]


@app.get("/api/signouts/{signout_id}", response_model=Signout)
def get_signout(
    signout_id: str,
    view: Literal["author", "reviewer"] = Query(default="reviewer"),
) -> Signout:
    _ = view
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return signout


@app.patch("/api/signouts/{signout_id}", response_model=Signout)
def update_signout(signout_id: str, payload: SignoutUpdate) -> Signout:
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")

    normalized_update = _normalized_signout_data(payload)
    updated_signout = signout.model_copy(update=normalized_update)
    SIGNOUTS[signout_id] = updated_signout
    return updated_signout


@app.post("/api/signouts/{signout_id}/score", response_model=RubricScore)
def score_stored_signout(signout_id: str) -> RubricScore:
    signout = SIGNOUTS.get(signout_id)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return score_signout(signout)


@app.delete("/api/signouts/{signout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signout(signout_id: str) -> Response:
    signout = SIGNOUTS.pop(signout_id, None)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
