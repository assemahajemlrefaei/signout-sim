from fastapi.testclient import TestClient

from main import SIGNOUTS, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUTS.clear()


def payload(**overrides: object) -> dict:
    base = {
        "case_id": "case-1",
        "illness_severity": "Watcher",
        "patient_summary": "Patient with sepsis improving, continue close overnight monitoring.",
        "action_list": ["Trend lactate", "Monitor blood pressure"],
        "situational_awareness": ["Risk for hypotension", "Escalate if MAP < 65"],
        "contingency_plans": ["Give 500cc LR for hypotension", "Notify ICU if not responsive"],
        "receiver_synthesis": "I will monitor trends and escalate quickly if instability develops.",
        "free_text": "Family updated.",
    }
    base.update(overrides)
    return base


def create_signout(**overrides: object) -> dict:
    response = client.post("/api/signouts", json=payload(**overrides))
    assert response.status_code == 201
    return response.json()


def test_create_signout_returns_record_with_id_and_created_at() -> None:
    response = client.post("/api/signouts", json=payload())

    assert response.status_code == 201
    body = response.json()
    assert body["signout_id"]
    assert isinstance(body["created_at"], str)
    assert isinstance(body["action_list"], list)


def test_list_pagination_and_case_filter() -> None:
    create_signout(case_id="case-a")
    create_signout(case_id="case-b")
    create_signout(case_id="case-a")

    filtered = client.get("/api/signouts?case_id=case-a")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 2
    assert all(item["case_id"] == "case-a" for item in filtered.json())

    paged = client.get("/api/signouts?limit=1&offset=1")
    assert paged.status_code == 200
    assert len(paged.json()) == 1


def test_newline_normalization() -> None:
    created = create_signout(
        action_list="a\n\n b ",
        situational_awareness=" first\n\nsecond ",
        contingency_plans=" only-one ",
    )

    assert created["action_list"] == ["a", "b"]
    assert created["situational_awareness"] == ["first", "second"]
    assert created["contingency_plans"] == ["only-one"]


def test_score_contract() -> None:
    created = create_signout()

    response = client.post(f"/api/signouts/{created['signout_id']}/score")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "strengths",
        "improvements",
        "missing_critical",
        "subscores",
        "total_score",
        "rubric_version",
    }
    assert body["rubric_version"] == "v0.1"
    assert set(body["subscores"].keys()) == {
        "illness_severity",
        "patient_summary",
        "action_list",
        "situational_awareness",
        "contingency_plans",
        "receiver_synthesis",
    }


def test_weak_lower_than_strong() -> None:
    weak = create_signout(
        patient_summary="short",
        action_list=[],
        situational_awareness=[],
        contingency_plans=[],
        receiver_synthesis="brief",
    )
    strong = create_signout(
        patient_summary=(
            "Complex septic shock case improving on broad-spectrum antibiotics with trending lactate, "
            "clear overnight tasks, and explicit escalation criteria for deterioration."
        ),
        action_list=["Recheck lactate at 2am", "Trend MAP q1h", "Call senior if MAP < 65"],
        situational_awareness=["May decompensate", "Rising oxygen needs signal worsening"],
        contingency_plans=["Fluid bolus for hypotension", "ICU consult if persistent hypotension"],
        receiver_synthesis="I will track hemodynamics, execute tasks, and escalate rapidly if thresholds are crossed.",
    )

    weak_score = client.post(f"/api/signouts/{weak['signout_id']}/score").json()["total_score"]
    strong_score = client.post(f"/api/signouts/{strong['signout_id']}/score").json()["total_score"]

    assert weak_score < strong_score
