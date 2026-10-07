"""BOBAI HR settings layered over the unchanged Horilla settings."""

from horilla.settings import *  # noqa: F403

BRAND_NAME = "BOBAI HR"
BRAND_LOGO = "bobai/images/logo.png"

# Preserve shared lists: upstream apps register integrations and template
# processors on horilla.settings during Django app initialization.
INSTALLED_APPS.insert(0, "bobai.apps.BobaiConfig")  # noqa: F405
TEMPLATES[0]["OPTIONS"]["context_processors"].append("bobai.context_processors.branding")

# The Docker development stack must never silently fall back to SQLite.
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":  # noqa: F405
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("BOBAI HR requires PostgreSQL. Start with docker compose up --build.")
