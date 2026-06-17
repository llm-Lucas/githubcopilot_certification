import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client, reset_activities):
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestActivitiesListEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange
        expected_activity_names = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Club",
            "Music Band",
            "Debate Team",
            "Science Club"
        ]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) == 9
        for activity_name in expected_activity_names:
            assert activity_name in data

    def test_get_activities_returns_activity_details(self, client, reset_activities):
        # Arrange
        expected_keys = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_details in data.items():
            for key in expected_keys:
                assert key in activity_details

    def test_get_activities_returns_participants_list(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")
        data = response.json()
        participants = data[activity_name]["participants"]

        # Assert
        assert response.status_code == 200
        assert isinstance(participants, list)
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        # Arrange
        activity_name = "Art Club"
        email = "new_student@mergington.edu"
        initial_participants = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        updated_activities = client.get("/activities").json()
        assert email in updated_activities[activity_name]["participants"]
        assert len(updated_activities[activity_name]["participants"]) == initial_participants + 1

    def test_signup_duplicate_email(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_not_found(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_missing_email_parameter(self, client, reset_activities):
        # Arrange
        activity_name = "Art Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 422  # Unprocessable Entity (missing required param)


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{participant_email} endpoint"""

    def test_remove_participant_success(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Removed {email} from {activity_name}"

        # Verify participant was removed
        updated_activities = client.get("/activities").json()
        assert email not in updated_activities[activity_name]["participants"]
        assert len(updated_activities[activity_name]["participants"]) == initial_count - 1

    def test_remove_participant_not_found_in_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Art Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_participant_activity_not_found(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_last_participant(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "alex@mergington.edu"  # Only participant

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 200
        
        # Verify activity now has no participants
        updated_activities = client.get("/activities").json()
        assert len(updated_activities[activity_name]["participants"]) == 0
