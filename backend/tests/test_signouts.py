from fastapi.testclient import TestClient

from main import SIGNOUTS, app


client = TestClient(app)


def setup_function() -> None:
    SIGNOUTS.clear()


def _create_signout() -> dict:
    response = client.post(
        "/api/signouts",
        json={
            "patient_name": "Jane Doe",
            "author_id": "resident-1",
            "summary": "Overnight follow-up for blood cultures",
        },
    )
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
    first = _create_signout()
    second = _create_signout()

    response = client.get("/api/signouts?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json() == [second]
    assert response.json() != [first]
