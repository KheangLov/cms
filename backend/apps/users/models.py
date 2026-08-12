from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Email is the identifier — CMS_BUILD_PROMPT.md §5.4 ("email/password auth")."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """CMS_BUILD_PROMPT.md §4 — locale/theme preference, 2FA flag, is_superuser bypasses
    all permission checks (Django's native behavior, nothing custom needed for that)."""

    username = None
    email = models.EmailField(unique=True)

    LOCALE_CHOICES = [("en", "English"), ("km", "Khmer")]
    locale_preference = models.CharField(max_length=8, choices=LOCALE_CHOICES, default="en")

    THEME_CHOICES = [("system", "System"), ("light", "Light"), ("dark", "Dark")]
    theme_preference = models.CharField(max_length=8, choices=THEME_CHOICES, default="system")

    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        permissions = [
            ("manage_users", "Can manage users and roles"),
        ]

    def __str__(self):
        return self.email
