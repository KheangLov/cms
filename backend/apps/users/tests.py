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
        # row (replay protection), so this needs a code from a *different* time step
        # — without actually sleeping the test.
        #
        # Target the start of the next 30s step explicitly rather than "now + 31s":
        # +31s lands one step ahead for 29 of every 30 seconds, but two steps ahead
        # when the clock is in the final second of a step, which django_otp rejects
        # (its default tolerance is +/-1 step). That made this test fail ~3% of runs.
        import time

        step = 30
        next_step_start = (int(time.time()) // step + 1) * step
        code2 = pyotp.TOTP(secret).at(next_step_start)
        verify = client.post(
            "/api/v1/auth/2fa/verify/",
            {"pending_token": login2.data["pending_token"], "code": code2},
        )
        assert verify.status_code == 200
        assert "access" in verify.data


@pytest.mark.django_db
class TestSelfServiceProfile:
    """Regression: MeView only supported GET — there was no way for a user to edit
    their own name/avatar/locale/theme, and UserSerializer didn't expose avatar at
    all. Both the missing method and the missing field are covered here."""

    def test_patch_updates_own_profile(self):
        User.objects.create_user(email="profile@test.local", password="S3cure!2026")
        client = APIClient()
        login = client.post("/api/v1/auth/login/", {"email": "profile@test.local", "password": "S3cure!2026"})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        resp = client.patch(
            "/api/v1/auth/me/",
            {"first_name": "Pat", "last_name": "Doe", "locale_preference": "km", "theme_preference": "dark"},
            format="json",
        )

        assert resp.status_code == 200
        assert resp.data["first_name"] == "Pat"
        assert resp.data["locale_preference"] == "km"
        assert resp.data["theme_preference"] == "dark"
        assert "avatar" in resp.data

        user = User.objects.get(email="profile@test.local")
        assert user.first_name == "Pat"
        assert user.locale_preference == "km"

    def test_patch_cannot_escalate_privileges(self):
        """UserSerializer.read_only_fields must still hold on the self-service path
        — a plain PATCH /auth/me/ is not the manage_users-gated admin endpoint."""
        User.objects.create_user(email="noescalate@test.local", password="S3cure!2026")
        client = APIClient()
        login = client.post(
            "/api/v1/auth/login/", {"email": "noescalate@test.local", "password": "S3cure!2026"}
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        resp = client.patch("/api/v1/auth/me/", {"is_superuser": True, "is_staff": True}, format="json")

        assert resp.status_code == 200
        user = User.objects.get(email="noescalate@test.local")
        assert user.is_superuser is False
        assert user.is_staff is False

    def test_anonymous_cannot_patch_profile(self):
        resp = APIClient().patch("/api/v1/auth/me/", {"first_name": "Nope"}, format="json")
        assert resp.status_code == 401


def _superuser_client(email="root@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.mark.django_db
class TestAdminUserManagement:
    """Regression: UserAdminSerializer.update() looped over validated_data with a
    plain setattr(), which Django rejects for the `groups` many-to-many field
    ("Direct assignment to the forward side of a many-to-many set is prohibited").
    Since the admin Users page always sends `groups` on save (even unchanged, e.g.
    []), editing *any* existing user through the UI 500'd — role assignment was
    completely broken. create() already special-cased it correctly; update() didn't."""

    def test_editing_a_user_assigns_groups_without_500(self):
        from django.contrib.auth.models import Group

        client = _superuser_client()
        role = Group.objects.create(name="Custom Test Role")
        target = User.objects.create_user(email="member@test.local", password="S3cure!2026")

        resp = client.patch(f"/api/v1/users/{target.id}/", {"groups": [role.id]}, format="json")

        assert resp.status_code == 200
        target.refresh_from_db()
        assert list(target.groups.values_list("id", flat=True)) == [role.id]

    def test_editing_a_user_with_empty_groups_list_still_works(self):
        """The admin form always includes `groups` in its PATCH body, even when
        it's just []  — that must not 500 either."""
        client = _superuser_client("root2@test.local")
        target = User.objects.create_user(email="member2@test.local", password="S3cure!2026")

        resp = client.patch(
            f"/api/v1/users/{target.id}/",
            {"first_name": "Updated", "groups": []},
            format="json",
        )

        assert resp.status_code == 200
        target.refresh_from_db()
        assert target.first_name == "Updated"
