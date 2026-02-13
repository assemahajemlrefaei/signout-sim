from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_list_cases_returns_summaries() -> None:
    response = client.get("/api/cases")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 2
    assert payload[0].keys() == {"case_id", "title", "tags", "difficulty"}


def test_case_detail_practice_includes_hidden_truth() -> None:
    response = client.get("/api/cases/case-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "case-001"
    assert "snapshot" in payload
    assert "hidden_truth" in payload


def test_case_detail_exam_hides_hidden_truth() -> None:
    response = client.get("/api/cases/case-001", params={"mode": "exam"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "case-001"
    assert "snapshot" in payload
    assert "hidden_truth" not in payload
