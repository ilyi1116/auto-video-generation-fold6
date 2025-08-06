from fastapi.testclient import TestClient


class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_user_success(self, client: TestClient, sample_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_user_duplicate_email(self, client: TestClient, sample_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/v1/register", json=sample_user_data)

        # Try to register with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "differentuser"

        response = client.post("/api/v1/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_user_duplicate_username(self, client: TestClient, sample_user_data):
        """Test registration with duplicate username"""
        # Register first user
        client.post("/api/v1/register", json=sample_user_data)

        # Try to register with same username
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response = client.post("/api/v1/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_user_invalid_password(self, client: TestClient, sample_user_data):
        """Test registration with invalid password"""
        invalid_data = sample_user_data.copy()
        invalid_data["password"] = "123"  # Too short

        response = client.post("/api/v1/register", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality"""

    def test_login_success(self, client: TestClient, sample_user_data):
        """Test successful login"""
        # Register user
        client.post("/api/v1/register", json=sample_user_data)

        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        }
        response = client.post("/api/v1/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_email(self, client: TestClient, sample_user_data):
        """Test login with invalid email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword",
        }
        response = client.post("/api/v1/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_password(self, client: TestClient, sample_user_data):
        """Test login with invalid password"""
        # Register user
        client.post("/api/v1/register", json=sample_user_data)

        # Try login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "wrongpassword",
        }
        response = client.post("/api/v1/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestUserProfile:
    """Test user profile functionality"""

    def test_get_current_user(self, client: TestClient, sample_user_data):
        """Test getting current user profile"""
        # Register and login
        client.post("/api/v1/register", json=sample_user_data)
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Get profile
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/api/v1/me")
        assert response.status_code == 403  # No authorization header

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        response = client.get("/api/v1/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401

    def test_update_user_profile(self, client: TestClient, sample_user_data):
        """Test updating user profile"""
        # Register and login
        client.post("/api/v1/register", json=sample_user_data)
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Update profile
        update_data = {"full_name": "Updated Name", "bio": "This is my bio"}
        response = client.put(
            "/api/v1/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "This is my bio"


class TestPasswordManagement:
    """Test password management functionality"""

    def test_change_password_success(self, client: TestClient, sample_user_data):
        """Test successful password change"""
        # Register and login
        client.post("/api/v1/register", json=sample_user_data)
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Change password
        password_change_data = {
            "current_password": sample_user_data["password"],
            "new_password": "newpassword123",
        }
        response = client.post(
            "/api/v1/change-password",
            json=password_change_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"]

        # Test login with new password
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": sample_user_data["email"],
                "password": "newpassword123",
            },
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, sample_user_data):
        """Test password change with wrong current password"""
        # Register and login
        client.post("/api/v1/register", json=sample_user_data)
        login_response = client.post(
            "/api/v1/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Try to change password with wrong current password
        password_change_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        }
        response = client.post(
            "/api/v1/change-password",
            json=password_change_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
