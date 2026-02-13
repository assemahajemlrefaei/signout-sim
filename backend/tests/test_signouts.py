from fastapi.testclient import TestClient

from main import SIGNOUT_STORE, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUT_STORE.clear()


def make_payload(case_id: str = "case-123") -> dict[str, object]:
    return {
        "case_id": case_id,
        "illness_severity": "Watcher",
        "patient_summary": "Patient with respiratory distress.",
        "action_list": "Check vitals\nRepeat blood gas",
        "situational_awareness": ["On high-flow oxygen", "Family at bedside"],
        "contingency_plans": "If worsening, call PICU",
        "receiver_synthesis": "I will monitor oxygen requirements.",
        "free_text": "Optional note",
    }


def test_create_and_get_signout() -> None:
    create_response = client.post("/api/signouts", json=make_payload())
    assert create_response.status_code == 200

    signout_id = create_response.json()["signout_id"]

    get_response = client.get(f"/api/signouts/{signout_id}")
    assert get_response.status_code == 200

    payload = get_response.json()
    assert payload["id"] == signout_id
    assert payload["case_id"] == "case-123"
    assert payload["illness_severity"] == "Watcher"
    assert payload["action_list"] == ["Check vitals", "Repeat blood gas"]
    assert payload["contingency_plans"] == ["If worsening, call PICU"]


def test_list_signouts_by_case() -> None:
    first = client.post("/api/signouts", json=make_payload(case_id="case-list")).json()["signout_id"]
    second = client.post("/api/signouts", json=make_payload(case_id="case-list")).json()["signout_id"]
    client.post("/api/signouts", json=make_payload(case_id="case-other"))

    response = client.get("/api/signouts", params={"case_id": "case-list"})
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 2
    assert [item["id"] for item in items] == [first, second]
    assert all("created_at" in item for item in items)


def test_create_signout_validation_errors() -> None:
    bad_severity = make_payload()
    bad_severity["illness_severity"] = "Critical"

    response = client.post("/api/signouts", json=bad_severity)
    assert response.status_code == 422

    bad_list = make_payload()
    bad_list["action_list"] = 42

    response = client.post("/api/signouts", json=bad_list)
    assert response.status_code == 422
