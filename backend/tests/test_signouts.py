from fastapi.testclient import TestClient

from main import SIGNOUTS, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUTS.clear()


def _payload(
    *,
    case_id: str = "case-1",
    illness_severity: str = "Watcher",
    patient_summary: str = "65M with sepsis improving on cefepime; monitor overnight trends.",
    action_list: list[str] | str = ["Follow 2am lactate", "Repeat blood cultures if febrile"],
    situational_awareness: list[str] | str = ["Risk of hypotension", "Escalate if MAP < 65"],
    contingency_plans: list[str] | str = ["If hypotensive, give 500cc LR", "Call ICU if persistent"],
    receiver_synthesis: str = "I will trend vitals and lactate, then escalate for persistent hypotension.",
    free_text: str | None = "Family updated.",
) -> dict:
    return {
        "case_id": case_id,
        "illness_severity": illness_severity,
        "patient_summary": patient_summary,
        "action_list": action_list,
        "situational_awareness": situational_awareness,
        "contingency_plans": contingency_plans,
        "receiver_synthesis": receiver_synthesis,
        "free_text": free_text,
    }


def _create_signout(**kwargs: object) -> dict:
    response = client.post("/api/signouts", json=_payload(**kwargs))
    assert response.status_code == 201
    return response.json()


def test_list_signouts_supports_query_pagination() -> None:
    first = _create_signout(case_id="case-a")
    second = _create_signout(case_id="case-b")

    response = client.get("/api/signouts?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json() == [second]
    assert response.json() != [first]


def test_create_signout_normalizes_multiline_fields() -> None:
    created = _create_signout(
        action_list="  Recheck CBC\n\nCall senior if Hb drops  ",
        situational_awareness=" Watch for bleeding ",
        contingency_plans="If unstable, activate rapid response\n",
    )

    assert created["action_list"] == ["Recheck CBC", "Call senior if Hb drops"]
    assert created["situational_awareness"] == ["Watch for bleeding"]
    assert created["contingency_plans"] == ["If unstable, activate rapid response"]


def test_score_returns_rubric_contract() -> None:
    created = _create_signout()

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


def test_weak_signout_scores_lower_than_strong_signout() -> None:
    strong = _create_signout(case_id="case-strong")
    weak = _create_signout(
        case_id="case-weak",
        illness_severity="Stable",
        patient_summary="Short summary.",
        action_list="",
        situational_awareness="",
        contingency_plans="",
        receiver_synthesis="ok",
    )

    strong_score = client.post(f"/api/signouts/{strong['signout_id']}/score").json()["total_score"]
    weak_score = client.post(f"/api/signouts/{weak['signout_id']}/score").json()["total_score"]

    assert weak_score < strong_score
