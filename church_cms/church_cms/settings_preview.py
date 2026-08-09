from .settings import *  # noqa

# Local-only overrides for visual verification (no Redis in sandbox)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "zova-preview",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
