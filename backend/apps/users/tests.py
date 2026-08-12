import pyotp
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuth:
    def test_register_and_login(self):
        client = APIClient()
        resp = client.post("/api/v1/auth/register/", {"email": "a@example.com", "password": "S3cure!2026"})
        assert resp.status_code == 201
        assert resp.data["user"]["email"] == "a@example.com"

        resp = client.post("/api/v1/auth/login/", {"email": "a@example.com", "password": "S3cure!2026"})
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_login_wrong_password_rejected(self):
        User.objects.create_user(email="b@example.com", password="Correct!2026")
        client = APIClient()
        resp = client.post("/api/v1/auth/login/", {"email": "b@example.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_me_requires_auth(self):
        client = APIClient()
        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 401

    def test_me_with_token(self):
        User.objects.create_user(email="c@example.com", password="S3cure!2026")
        client = APIClient()
        login = client.post("/api/v1/auth/login/", {"email": "c@example.com", "password": "S3cure!2026"})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        assert resp.data["email"] == "c@example.com"


@pytest.mark.django_db
class TestTwoFactor:
    """Regression test for the CMS_BUILD_PROMPT.md §9 flow — including the hex-
    vs-base32 secret bug found during manual verification (pyotp would fail to
    even construct a TOTP object from a bad secret, so this test would have
    caught it)."""

    def test_full_2fa_flow(self):
        User.objects.create_user(email="d@example.com", password="S3cure!2026")
        client = APIClient()
        login = client.post("/api/v1/auth/login/", {"email": "d@example.com", "password": "S3cure!2026"})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        setup = client.post("/api/v1/auth/2fa/setup/")
        assert setup.status_code == 200
        secret = setup.data["secret"]

        code = pyotp.TOTP(secret).now()
        confirm = client.post("/api/v1/auth/2fa/confirm/", {"code": code})
        assert confirm.status_code == 200
        assert len(confirm.data["recovery_codes"]) == 10

        user = User.objects.get(email="d@example.com")
        assert user.is_2fa_enabled is True

        client.credentials()  # log out the client side, force a fresh login
        login2 = client.post("/api/v1/auth/login/", {"email": "d@example.com", "password": "S3cure!2026"})
        assert login2.data["requires_2fa"] is True

        # django_otp correctly rejects reusing the exact same TOTP code twice in a
        # row (replay protection) — .at(...) 31s ahead guarantees a different
        # time-step without actually sleeping the test.
        import time

        code2 = pyotp.TOTP(secret).at(time.time() + 31)
        verify = client.post(
            "/api/v1/auth/2fa/verify/",
            {"pending_token": login2.data["pending_token"], "code": code2},
        )
        assert verify.status_code == 200
        assert "access" in verify.data
