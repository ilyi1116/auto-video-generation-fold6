"""
認證服務路由測試
測試所有認證相關的 API 端點
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.schemas import UserCreate, Token


@pytest.mark.unit
class TestAuthRouters:
    """認證路由單元測試"""

    @pytest.fixture
    async def client(self) -> AsyncClient:
        """創建測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """測試用戶註冊成功"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "full_name": "New User",
        }

        with (
            patch("app.crud.create_user") as mock_create,
            patch("app.crud.get_user_by_email") as mock_get_email,
            patch("app.crud.get_user_by_username") as mock_get_username,
        ):

            mock_get_email.return_value = None
            mock_get_username.return_value = None
            mock_create.return_value = {
                "id": 1,
                "email": user_data["email"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "is_active": True,
                "is_verified": False,
            }

            response = await client.post("/auth/register", json=user_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["username"] == user_data["username"]
            assert "password" not in data  # 確保密碼不被返回

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, client: AsyncClient):
        """測試用戶註冊 - 電子郵件已存在"""
        user_data = {
            "email": "existing@example.com",
            "username": "newuser",
            "password": "securepassword123",
            "full_name": "New User",
        }

        with patch("app.crud.get_user_by_email") as mock_get_email:
            mock_get_email.return_value = {"id": 1, "email": "existing@example.com"}

            response = await client.post("/auth/register", json=user_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """測試用戶登入成功"""
        login_data = {"username": "testuser@example.com", "password": "correctpassword"}

        with (
            patch("app.crud.get_user_by_email") as mock_get_user,
            patch("app.security.verify_password") as mock_verify,
            patch("app.security.create_access_token") as mock_token,
            patch("app.security.create_refresh_token") as mock_refresh,
        ):

            mock_get_user.return_value = {
                "id": 1,
                "email": "testuser@example.com",
                "hashed_password": "hashed_password",
                "is_active": True,
                "is_verified": True,
            }
            mock_verify.return_value = True
            mock_token.return_value = "access_token_123"
            mock_refresh.return_value = "refresh_token_123"

            response = await client.post("/auth/login", data=login_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == "access_token_123"
            assert data["refresh_token"] == "refresh_token_123"
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """測試用戶登入 - 無效憑證"""
        login_data = {"username": "testuser@example.com", "password": "wrongpassword"}

        with (
            patch("app.crud.get_user_by_email") as mock_get_user,
            patch("app.security.verify_password") as mock_verify,
        ):

            mock_get_user.return_value = {
                "id": 1,
                "email": "testuser@example.com",
                "hashed_password": "hashed_password",
                "is_active": True,
            }
            mock_verify.return_value = False

            response = await client.post("/auth/login", data=login_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient):
        """測試用戶登入 - 帳戶未啟用"""
        login_data = {"username": "inactive@example.com", "password": "correctpassword"}

        with (
            patch("app.crud.get_user_by_email") as mock_get_user,
            patch("app.security.verify_password") as mock_verify,
        ):

            mock_get_user.return_value = {
                "id": 1,
                "email": "inactive@example.com",
                "is_active": False,
            }
            mock_verify.return_value = True

            response = await client.post("/auth/login", data=login_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Inactive user" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient):
        """測試刷新令牌成功"""
        refresh_data = {"refresh_token": "valid_refresh_token"}

        with (
            patch("app.security.verify_refresh_token") as mock_verify,
            patch("app.crud.get_user") as mock_get_user,
            patch("app.security.create_access_token") as mock_token,
        ):

            mock_verify.return_value = {"user_id": 1}
            mock_get_user.return_value = {
                "id": 1,
                "email": "testuser@example.com",
                "is_active": True,
            }
            mock_token.return_value = "new_access_token"

            response = await client.post("/auth/refresh", json=refresh_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == "new_access_token"
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """測試刷新令牌 - 無效令牌"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}

        with patch("app.security.verify_refresh_token") as mock_verify:
            mock_verify.return_value = None

            response = await client.post("/auth/refresh", json=refresh_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client: AsyncClient):
        """測試獲取當前用戶信息成功"""
        headers = {"Authorization": "Bearer valid_access_token"}

        with patch("app.dependencies.get_current_user") as mock_get_current:
            mock_get_current.return_value = {
                "id": 1,
                "email": "testuser@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "is_active": True,
                "is_verified": True,
            }

            response = await client.get("/auth/me", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "testuser@example.com"
            assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """測試獲取當前用戶信息 - 未授權"""
        response = await client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        """測試用戶登出成功"""
        headers = {"Authorization": "Bearer valid_access_token"}

        with (
            patch("app.dependencies.get_current_user") as mock_get_current,
            patch("app.crud.invalidate_user_tokens") as mock_invalidate,
        ):

            mock_get_current.return_value = {"id": 1}
            mock_invalidate.return_value = True

            response = await client.post("/auth/logout", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            assert "Successfully logged out" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient):
        """測試修改密碼成功"""
        headers = {"Authorization": "Bearer valid_access_token"}
        password_data = {"current_password": "oldpassword", "new_password": "newpassword123"}

        with (
            patch("app.dependencies.get_current_user") as mock_get_current,
            patch("app.security.verify_password") as mock_verify,
            patch("app.crud.update_user_password") as mock_update,
        ):

            mock_get_current.return_value = {"id": 1, "hashed_password": "hashed_old_password"}
            mock_verify.return_value = True
            mock_update.return_value = True

            response = await client.put(
                "/auth/change-password", headers=headers, json=password_data
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Password updated successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient):
        """測試修改密碼 - 當前密碼錯誤"""
        headers = {"Authorization": "Bearer valid_access_token"}
        password_data = {"current_password": "wrongpassword", "new_password": "newpassword123"}

        with (
            patch("app.dependencies.get_current_user") as mock_get_current,
            patch("app.security.verify_password") as mock_verify,
        ):

            mock_get_current.return_value = {"id": 1, "hashed_password": "hashed_old_password"}
            mock_verify.return_value = False

            response = await client.put(
                "/auth/change-password", headers=headers, json=password_data
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Incorrect current password" in response.json()["detail"]


@pytest.mark.integration
class TestAuthIntegration:
    """認證服務整合測試"""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client: AsyncClient, db_session):
        """測試完整的認證流程：註冊 -> 登入 -> 獲取信息 -> 登出"""
        # 註冊用戶
        user_data = {
            "email": "flowtest@example.com",
            "username": "flowtest",
            "password": "testpassword123",
            "full_name": "Flow Test User",
        }

        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # 登入
        login_data = {"username": user_data["email"], "password": user_data["password"]}

        login_response = await client.post("/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK

        token_data = login_response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # 獲取用戶信息
        me_response = await client.get("/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK

        user_info = me_response.json()
        assert user_info["email"] == user_data["email"]

        # 登出
        logout_response = await client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK
