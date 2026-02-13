from fastapi.testclient import TestClient

from main import SIGNOUTS, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUTS.clear()


def _create_signout(overrides: dict | None = None) -> dict:
    payload = {
        "patient_name": "Jane Doe",
        "author_id": "resident-1",
        "summary": "Dx: pneumonia, stable on IV antibiotics and oxygen",
        "illness_severity": "Watcher",
        "patient_summary": "Dx pneumonia, stable respiratory status, on IV antibiotics and O2",
        "action_list": ["Check temp at 02:00", "Call if SBP<90"],
        "situational_awareness": ["If worsening O2 needs, call senior", "Monitor HR trend"],
        "contingency_plans": ["If fever persists, reculture", "Call rapid response for BP drop"],
        "receiver_synthesis": "I will monitor vitals and reassess; I'll call if worsening.",
    }
    if overrides:
        payload.update(overrides)

    response = client.post("/api/signouts", json=payload)
    assert response.status_code == 201
    return response.json()


def test_get_signout_defaults_to_reviewer_view() -> None:
    signout = _create_signout()

    response = client.get(f"/api/signouts/{signout['signout_id']}")

    assert response.status_code == 200
    assert response.json() == signout


def test_get_signout_allows_author_view() -> None:
    signout = _create_signout()

    response = client.get(f"/api/signouts/{signout['signout_id']}?view=author")

    assert response.status_code == 200
    assert response.json() == signout


def test_get_signout_rejects_unknown_view() -> None:
    signout = _create_signout()

    response = client.get(f"/api/signouts/{signout['signout_id']}?view=unknown")

    assert response.status_code == 422


def test_list_signouts_supports_query_pagination() -> None:
    first = _create_signout({"patient_name": "First"})
    second = _create_signout({"patient_name": "Second"})

    response = client.get("/api/signouts?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json() == [second]
    assert response.json() != [first]


def test_score_returns_expected_keys_and_rubric_version() -> None:
    signout = _create_signout()

    response = client.post(f"/api/signouts/{signout['signout_id']}/score")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "strengths",
        "improvements",
        "missing_critical",
        "subscores",
        "total_score",
        "rubric_version",
    }
    assert payload["rubric_version"] == "v0.1"


def test_weak_signout_scores_lower_than_strong_signout() -> None:
    weak = _create_signout(
        {
            "summary": "follow up",
            "illness_severity": "Stable",
            "patient_summary": "",
            "action_list": [],
            "situational_awareness": [],
            "contingency_plans": [],
            "receiver_synthesis": "",
        }
    )
    strong = _create_signout({"patient_name": "Strong Patient"})

    weak_score = client.post(f"/api/signouts/{weak['signout_id']}/score").json()["total_score"]
    strong_score = client.post(f"/api/signouts/{strong['signout_id']}/score").json()["total_score"]

    assert weak_score < strong_score


def test_missing_lists_produce_improvement_feedback() -> None:
    signout = _create_signout(
        {
            "action_list": [],
            "situational_awareness": [],
            "contingency_plans": [],
        }
    )

    response = client.post(f"/api/signouts/{signout['signout_id']}/score")

    assert response.status_code == 200
    improvements = response.json()["improvements"]
    assert any("action_list" in item for item in improvements)
    assert any("situational_awareness" in item for item in improvements)
    assert any("contingency_plans" in item for item in improvements)
