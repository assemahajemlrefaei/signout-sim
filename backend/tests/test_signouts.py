from fastapi.testclient import TestClient

from main import SIGNOUTS, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUTS.clear()


def _payload(**overrides: object) -> dict:
    payload = {
        "case_id": "case-123",
        "illness_severity": "stable",
        "patient_summary": "Overnight follow-up for blood cultures",
        "action_list": ["Check repeat lactate"],
        "situational_awareness": ["Watch for fever"],
        "contingency_plans": ["If febrile, draw cultures"],
        "receiver_synthesis": "Will monitor overnight vitals and fever curve",
        "free_text": "Optional note",
    }
    payload.update(overrides)
    return payload


def _create_signout(**overrides: object) -> dict:
    response = client.post("/api/signouts", json=_payload(**overrides))
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
    first = _create_signout(case_id="case-1")
    second = _create_signout(case_id="case-2")

    response = client.get("/api/signouts?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json() == [second]
    assert response.json() != [first]


def test_create_signout_normalizes_newline_fields_to_lists() -> None:
    signout = _create_signout(
        action_list="task one\n\n task two ",
        situational_awareness="watch bp\nwatch o2",
        contingency_plans="if hypotensive, call ICU",
    )

    assert signout["action_list"] == ["task one", "task two"]
    assert signout["situational_awareness"] == ["watch bp", "watch o2"]
    assert signout["contingency_plans"] == ["if hypotensive, call ICU"]


def test_score_signout_uses_stored_record() -> None:
    signout = _create_signout(free_text=None)

    response = client.post(f"/api/signouts/{signout['signout_id']}/score")

    assert response.status_code == 200
    assert response.json()["signout_id"] == signout["signout_id"]
    assert response.json()["score"] == 0.83
