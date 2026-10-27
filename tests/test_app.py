import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client_and_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    return TestClient(app_module.app), activities


def test_get_activities_returns_activity_data_and_disables_caching(
    client_and_activities,
):
    # Arrange
    client, activities = client_and_activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client_and_activities):
    # Arrange
    client, activities = client_and_activities
    email = "new@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client_and_activities):
    # Arrange
    client, activities = client_and_activities
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
    assert activities["Chess Club"]["participants"] == [email]


def test_signup_rejects_unknown_activity(client_and_activities):
    # Arrange
    client, _ = client_and_activities

    # Act
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client_and_activities):
    # Arrange
    client, activities = client_and_activities
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_unregistered_participant(client_and_activities):
    # Arrange
    client, activities = client_and_activities
    email = "missing@mergington.edu"
    original_participants = activities["Chess Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities["Chess Club"]["participants"] == original_participants


def test_unregister_rejects_unknown_activity(client_and_activities):
    # Arrange
    client, _ = client_and_activities

    # Act
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": "new@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
