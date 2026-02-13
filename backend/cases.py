from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


class CaseSummary(BaseModel):
    case_id: str
    title: str
    tags: list[str]
    difficulty: str


class CaseSnapshot(BaseModel):
    one_liner: str
    active_problems: list[str]
    vitals: dict[str, str | int | float | bool | None]
    labs: dict[str, str | int | float | bool | None]
    meds: list[str]
    pending: list[str]
    code_status: str


class CaseHiddenTruth(BaseModel):
    diagnosis: str
    pitfalls: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class Case(BaseModel):
    case_id: str
    title: str
    tags: list[str]
    difficulty: str
    snapshot: CaseSnapshot
    hidden_truth: CaseHiddenTruth


class CaseDetailPractice(BaseModel):
    case_id: str
    title: str
    tags: list[str]
    difficulty: str
    snapshot: CaseSnapshot
    hidden_truth: CaseHiddenTruth


class CaseDetailExam(BaseModel):
    case_id: str
    title: str
    tags: list[str]
    difficulty: str
    snapshot: CaseSnapshot


DATA_FILE = Path(__file__).resolve().parents[1] / "SPEC" / "03_CASES_SEED.json"


@lru_cache(maxsize=1)
def load_cases() -> dict[str, Case]:
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {item["case_id"]: Case.model_validate(item) for item in raw["cases"]}


def list_case_summaries() -> list[CaseSummary]:
    return [
        CaseSummary(
            case_id=case.case_id,
            title=case.title,
            tags=case.tags,
            difficulty=case.difficulty,
        )
        for case in load_cases().values()
    ]


def get_case(case_id: str) -> Case | None:
    return load_cases().get(case_id)
