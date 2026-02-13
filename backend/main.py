from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from cases import (
    CaseDetailExam,
    CaseDetailPractice,
    CaseSummary,
    get_case,
    list_case_summaries,
    load_cases,
)


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="signout-sim-backend")


@app.on_event("startup")
def startup_load_cases() -> None:
    load_cases()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/cases", response_model=list[CaseSummary])
def get_cases() -> list[CaseSummary]:
    return list_case_summaries()


@app.get("/api/cases/{case_id}", response_model=CaseDetailPractice | CaseDetailExam)
def get_case_detail(
    case_id: str,
    mode: str = Query(default="practice", pattern="^(practice|exam)$"),
) -> CaseDetailPractice | CaseDetailExam:
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    if mode == "exam":
        return CaseDetailExam(
            case_id=case.case_id,
            title=case.title,
            tags=case.tags,
            difficulty=case.difficulty,
            snapshot=case.snapshot,
        )

    return CaseDetailPractice(
        case_id=case.case_id,
        title=case.title,
        tags=case.tags,
        difficulty=case.difficulty,
        snapshot=case.snapshot,
        hidden_truth=case.hidden_truth,
    )
