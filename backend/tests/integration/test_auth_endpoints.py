"""
认证 API 集成测试
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    """认证相关接口测试"""

    async def test_login_success(self, client: AsyncClient, student_user):
        """正常登录应返回 Token"""
        res = await client.post("/api/v1/auth/login", json={
            "username": "test_student",
            "password": "Student@123456",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["username"] == "test_student"

    async def test_login_wrong_password(self, client: AsyncClient, student_user):
        """密码错误应返回 401"""
        res = await client.post("/api/v1/auth/login", json={
            "username": "test_student",
            "password": "WrongPassword",
        })
        assert res.status_code == 401

    async def test_login_unknown_user(self, client: AsyncClient):
        """不存在的用户应返回 401"""
        res = await client.post("/api/v1/auth/login", json={
            "username": "nobody",
            "password": "any",
        })
        assert res.status_code == 401

    async def test_get_me(self, client: AsyncClient, student_token: str):
        """已登录用户可获取自身信息"""
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["username"] == "test_student"

    async def test_get_me_without_token(self, client: AsyncClient):
        """未登录应返回 401"""
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401

    async def test_logout(self, client: AsyncClient, student_token: str):
        """已登录用户可退出登录"""
        res = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 200
