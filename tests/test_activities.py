from fastapi.testclient import TestClient
import pytest
import copy

from src.app import app, activities

@pytest.fixture(autouse=True)
def restore_activities():
    """Backup and restore the in-memory activities dict between tests."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    client = TestClient(app)

    resp = client.get("/activities")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_delete_flow():
    client = TestClient(app)

    activity = "Unit Test Activity"
    activities.setdefault(activity, {
        "description": "test activity",
        "schedule": "now",
        "max_participants": 5,
        "participants": []
    })

    email = "tester@example.com"
    # Ensure a clean start
    if email in activities[activity]["participants"]:
        activities[activity]["participants"].remove(email)

    # Sign up
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in activities[activity]["participants"]

    # Duplicate sign up -> 400
    resp_dup = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp_dup.status_code == 400

    # Delete participant
    resp_del = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp_del.status_code == 200
    assert email not in activities[activity]["participants"]

    # Deleting again -> 404
    resp_del2 = client.delete(f"/activities/{activity}/participants", params={"email": email})
    assert resp_del2.status_code == 404


def test_signup_nonexistent_activity_returns_404():
    client = TestClient(app)
    resp = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404


def test_delete_nonexistent_activity_returns_404():
    client = TestClient(app)
    resp = client.delete("/activities/Nonexistent/participants", params={"email": "a@b.com"})
    assert resp.status_code == 404
