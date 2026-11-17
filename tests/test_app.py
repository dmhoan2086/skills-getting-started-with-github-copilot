from copy import deepcopy

import pytest


def test_get_activities(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_root_redirect(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new.student@mergington.edu"
    original_participants = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activities_response.status_code == 200
    assert activities_response.json()["Chess Club"]["participants"] == [
        *original_participants, email
    ]


def test_duplicate_signup_does_not_change_participants(client, activity_data):
    # Arrange
    original_participants = activity_data["Chess Club"]["participants"].copy()
    email = original_participants[0]

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == original_participants


@pytest.mark.parametrize("method", ["post", "delete"])
def test_unknown_activity(client, activity_data, method):
    # Arrange
    original_data = deepcopy(activity_data)
    email = "student@mergington.edu"

    # Act
    response = client.request(
        method, "/activities/Unknown Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data == original_data


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    original_participants = activity_data["Chess Club"]["participants"].copy()
    email = original_participants[0]

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert activities_response.status_code == 200
    assert activities_response.json()["Chess Club"]["participants"] == [
        participant for participant in original_participants if participant != email
    ]


def test_unregister_nonparticipant_does_not_change_participants(client, activity_data):
    # Arrange
    original_participants = activity_data["Chess Club"]["participants"].copy()
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student not signed up for this activity"}
    assert activity_data["Chess Club"]["participants"] == original_participants


@pytest.mark.parametrize("method", ["post", "delete"])
def test_missing_email_is_rejected(client, activity_data, method):
    # Arrange
    original_data = deepcopy(activity_data)
    url = "/activities/Chess Club/signup"

    # Act
    response = client.request(method, url)

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert activity_data == original_data
