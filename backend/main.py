from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SignoutBase(BaseModel):
    patient_name: str
    author_id: str
    summary: str


class SignoutCreate(SignoutBase):
    pass


class SignoutUpdate(BaseModel):
    patient_name: str | None = None
    author_id: str | None = None
    summary: str | None = None


class Signout(SignoutBase):
    signout_id: str


app = FastAPI(title="signout-sim-backend")

SIGNOUTS: dict[str, Signout] = {}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/signouts", response_model=Signout, status_code=status.HTTP_201_CREATED)
def create_signout(payload: SignoutCreate) -> Signout:
    signout = Signout(signout_id=str(uuid4()), **payload.model_dump())
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

    updated = signout.model_copy(update=payload.model_dump(exclude_unset=True))
    SIGNOUTS[signout_id] = updated
    return updated


@app.delete("/api/signouts/{signout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signout(signout_id: str) -> Response:
    signout = SIGNOUTS.pop(signout_id, None)
    if signout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signout not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
