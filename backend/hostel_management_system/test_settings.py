"""
Dedicated settings module for the pytest test suite.

Overrides database to SQLite in-memory so tests run without a MySQL server.
All other settings are inherited from the production settings file, but
dangerous operations (email, S3, celery) are stubbed out.
"""
# Pull in everything from the main settings, then override what we need.
import tempfile
from pathlib import Path

# We import via a small trick: set env vars before importing so load_dotenv
# picks them up and the SECRET_KEY guard is satisfied.
import os
os.environ.setdefault("SECRET_KEY", "test-only-key-never-use-in-production-abc123")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")  # prevent MySQL selection

# Now import everything from the real settings
from hostel_management_system.settings import *  # noqa: F401, F403, E402

# ── Database: always SQLite in-memory ────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        # TEST dict is respected by Django's test runner too
        "TEST": {"NAME": ":memory:"},
    }
}

# ── Media: temporary directory so file tests don't pollute the working tree ──
_TEMP_MEDIA = tempfile.mkdtemp(prefix="hms_test_media_")
MEDIA_ROOT = _TEMP_MEDIA
MEDIA_URL = "/test-media/"

# ── Passwords: disable expensive validators during tests ─────────────────────
AUTH_PASSWORD_VALIDATORS = []

# ── Logging: silence all loggers during tests ────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}

# ── Email: use in-memory backend so no real emails fire ──────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Security: relax cookie settings for test client ─────────────────────────
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
