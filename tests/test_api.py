"""
Тесты для веб-API с использованием моков
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi import status
from httpx import ASGITransport, AsyncClient

from tests.conftest import _make_session_patcher
from web.main import app


class TestWorkoutsAPI:
    """Тесты API тренировок"""

    pytestmark = pytest.mark.asyncio

    async def test_get_workouts(self, api_client_admin):
        """Тест получения списка тренировок"""
        today = datetime.now().date()
        response = await api_client_admin.get(
            f"/api/workouts/?date_from={today}&date_to={today}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_create_workout_admin(self, api_client_admin, test_admin):
        """Тест создания тренировки админом"""
        workout_data = {
            "name": "Test Workout API",
            "description": "Test description",
            "datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 10,
            "trainer_id": test_admin.id,
        }

        response = await api_client_admin.post(
            "/api/workouts/",
            json=workout_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Workout API"
        assert data["duration"] == 60

    async def test_get_workout_by_id(self, api_client_admin, test_admin):
        """Тест получения тренировки по ID"""
        workout_data = {
            "name": "Test Get Workout",
            "datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 10,
            "trainer_id": test_admin.id,
        }
        create_response = await api_client_admin.post("/api/workouts/", json=workout_data)
        created_workout = create_response.json()

        response = await api_client_admin.get(f"/api/workouts/{created_workout['id']}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_workout["id"]
        assert data["name"] == "Test Get Workout"

    async def test_update_workout(self, api_client_admin, test_admin):
        """Тест обновления тренировки"""
        workout_data = {
            "name": "Original Workout",
            "datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 10,
            "trainer_id": test_admin.id,
        }
        create_response = await api_client_admin.post("/api/workouts/", json=workout_data)
        created_workout = create_response.json()

        update_data = {
            "name": "Updated Workout",
            "duration": 90,
        }

        response = await api_client_admin.put(
            f"/api/workouts/{created_workout['id']}",
            json=update_data,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Workout"
        assert data["duration"] == 90

    async def test_delete_workout(self, api_client_admin, test_admin):
        """Тест удаления тренировки"""
        workout_data = {
            "name": "To Delete",
            "datetime": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "max_participants": 10,
            "trainer_id": test_admin.id,
        }
        create_response = await api_client_admin.post("/api/workouts/", json=workout_data)
        created_workout = create_response.json()

        response = await api_client_admin.delete(f"/api/workouts/{created_workout['id']}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_delete_workouts_by_range(self, api_client_admin, test_admin):
        """Тест удаления тренировок по диапазону дат"""
        target_date = datetime.now() + timedelta(days=10)

        for i in range(3):
            workout_data = {
                "name": f"Range Test Workout {i}",
                "datetime": (target_date + timedelta(days=i)).isoformat(),
                "duration": 60,
                "max_participants": 10,
                "trainer_id": test_admin.id,
            }
            await api_client_admin.post("/api/workouts/", json=workout_data)

        date_from = target_date.date().isoformat()
        date_to = (target_date + timedelta(days=2)).date().isoformat()

        response = await api_client_admin.post(
            "/api/workouts/delete-by-range",
            json={"date_from": date_from, "date_to": date_to},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["deleted_workouts"] >= 3

    async def test_delete_by_range_invalid_dates(self, api_client_admin):
        """Тест: ошибка при неверном диапазоне дат (ОТ > ДО)"""
        response = await api_client_admin.post(
            "/api/workouts/delete-by-range",
            json={
                "date_from": "2025-12-31",
                "date_to": "2025-12-01",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_delete_by_range_trainer_forbidden(self, api_client_trainer):
        """Тест: тренер не может удалять по диапазону"""
        response = await api_client_trainer.post(
            "/api/workouts/delete-by-range",
            json={
                "date_from": "2025-12-01",
                "date_to": "2025-12-31",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUsersAPI:
    """Тесты API пользователей"""

    pytestmark = pytest.mark.asyncio

    async def test_get_users(self, api_client_admin):
        """Тест получения списка пользователей"""
        response = await api_client_admin.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "users" in data
        assert isinstance(data["users"], list)
        assert len(data["users"]) > 0

    async def test_get_user_by_id(self, api_client_admin, test_athlete):
        """Тест получения пользователя по ID"""
        response = await api_client_admin.get(f"/api/users/{test_athlete.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_athlete.id
        assert "telegram_id" in data

    async def test_update_user_role(self, api_client_admin, test_athlete):
        """Тест изменения роли пользователя (PATCH)"""
        response = await api_client_admin.patch(
            f"/api/users/{test_athlete.id}/role",
            json={"role": "trainer"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "trainer"

    async def test_set_trainer_web_password(self, api_client_admin, test_trainer, db_session):
        """Индивидуальный пароль: PATCH и проверка хеша в модели."""
        response = await api_client_admin.patch(
            f"/api/users/{test_trainer.id}/password",
            json={"password": "unique_web_pass_99"},
        )
        assert response.status_code == status.HTTP_200_OK
        await db_session.refresh(test_trainer)
        assert test_trainer.check_web_password("unique_web_pass_99")

    async def test_users_include_has_web_password(self, api_client_admin):
        response = await api_client_admin.get("/api/users/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for row in data["users"]:
            assert "has_web_password" in row


class TestAuthLogin:
    """Вход в веб: общий секрет или индивидуальный пароль."""

    pytestmark = pytest.mark.asyncio

    async def test_login_with_shared_secret_fallback(self, db_session, test_trainer):
        with _make_session_patcher(db_session):
            with patch(
                "web.api.auth.WebConfig.get_web_login_secret",
                return_value="shared_fallback_secret",
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    r = await client.post(
                        "/api/auth/login",
                        json={
                            "login": "test_trainer",
                            "secret_code": "shared_fallback_secret",
                        },
                    )
        assert r.status_code == status.HTTP_200_OK
        assert "access_token" in r.json()

    async def test_login_individual_password_rejects_shared(self, db_session, test_trainer):
        test_trainer.set_web_password("only_individual_ok")
        await db_session.commit()
        with _make_session_patcher(db_session):
            with patch(
                "web.api.auth.WebConfig.get_web_login_secret",
                return_value="shared_fallback_secret",
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    bad = await client.post(
                        "/api/auth/login",
                        json={
                            "login": "test_trainer",
                            "secret_code": "shared_fallback_secret",
                        },
                    )
                    ok = await client.post(
                        "/api/auth/login",
                        json={
                            "login": "test_trainer",
                            "secret_code": "only_individual_ok",
                        },
                    )
        assert bad.status_code == status.HTTP_401_UNAUTHORIZED
        assert ok.status_code == status.HTTP_200_OK


class TestPermissions:
    """Тесты прав доступа"""

    pytestmark = pytest.mark.asyncio

    async def test_trainer_cannot_change_roles(self, api_client_trainer, test_athlete):
        """Тест: тренер не может менять роли"""
        response = await api_client_trainer.patch(
            f"/api/users/{test_athlete.id}/role",
            json={"role": "admin"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_trainer_can_view_own_workouts(self, api_client_trainer):
        """Тест: тренер может видеть свои тренировки"""
        today = datetime.now().date()
        response = await api_client_trainer.get(
            f"/api/workouts/?date_from={today}&date_to={today}"
        )

        assert response.status_code == status.HTTP_200_OK


class TestGymSettingsAPI:
    """Настройки зала (лимит записей) — только админ."""

    pytestmark = pytest.mark.asyncio

    async def test_admin_get_settings(self, api_client_admin):
        r = await api_client_admin.get("/api/settings")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert "max_bookings_per_day" in data
        assert 1 <= data["max_bookings_per_day"] <= 20

    async def test_trainer_forbidden_settings(self, api_client_trainer):
        r = await api_client_trainer.get("/api/settings")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_patch_settings(self, api_client_admin):
        r = await api_client_admin.patch(
            "/api/settings",
            json={"max_bookings_per_day": 3},
        )
        assert r.status_code == status.HTTP_200_OK
        assert r.json()["max_bookings_per_day"] == 3


class TestBroadcastAPI:
    """Тесты API рассылки (только админ)"""

    pytestmark = pytest.mark.asyncio

    async def test_broadcast_forbidden_trainer(self, api_client_trainer):
        r = await api_client_trainer.post("/api/broadcast/", json={"message": "hello"})
        assert r.status_code == status.HTTP_403_FORBIDDEN

    @patch("web.api.broadcast.Bot")
    async def test_broadcast_empty_message(self, mock_bot, api_client_admin):
        r = await api_client_admin.post("/api/broadcast/", json={"message": "  "})
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    @patch("web.api.broadcast.Bot")
    async def test_broadcast_to_all(self, mock_bot, api_client_admin, test_athlete):
        mock_instance = mock_bot.return_value
        mock_instance.send_message = AsyncMock(return_value=None)

        r = await api_client_admin.post("/api/broadcast/", json={"message": "hello"})
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert data["success"] is True
        assert data["total"] >= 1
        assert mock_instance.send_message.called


class TestAnalyticsAPI:
    """Тесты API аналитики (только админ)"""

    pytestmark = pytest.mark.asyncio

    async def test_analytics_forbidden_trainer(self, api_client_trainer):
        r = await api_client_trainer.get("/api/analytics/heatmap")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    async def test_analytics_heatmap(self, api_client_admin):
        r = await api_client_admin.get("/api/analytics/heatmap")
        assert r.status_code == status.HTTP_200_OK
        data = r.json()
        assert "heatmap" in data
        assert "total_workouts" in data
