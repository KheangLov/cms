import json

from cryptography.fernet import Fernet
from django.conf import settings as django_settings
from django.db import models

from apps.common.models import TimestampedModel


def _fernet():
    return Fernet(django_settings.SETTINGS_ENCRYPTION_KEY.encode())


class Setting(TimestampedModel):
    """CMS_BUILD_PROMPT.md §5.8 — key/value(JSON) store, grouped by category.
    Secret values (AI API keys, etc.) are encrypted at rest via Fernet and never
    decrypted back out through the API — see SettingSerializer.to_representation."""

    key = models.SlugField(unique=True)
    raw_value = models.TextField(db_column="value")
    category = models.CharField(max_length=50, default="general")
    is_secret = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = [
            ("manage_settings", "Can manage site settings"),
        ]
        ordering = ["category", "key"]

    def __str__(self):
        return self.key

    @property
    def value(self):
        raw = self.raw_value
        if not raw:
            return None
        if self.is_secret:
            raw = _fernet().decrypt(raw.encode()).decode()
        return json.loads(raw)

    @value.setter
    def value(self, val):
        raw = json.dumps(val)
        if self.is_secret:
            raw = _fernet().encrypt(raw.encode()).decode()
        self.raw_value = raw
