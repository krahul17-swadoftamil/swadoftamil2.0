"""
Swad of Tamil — Django Backend Settings

API-first backend powering:
• React + Vite frontend
• Cloud kitchen & POS
• Ingredient SOP & stock discipline
• High-speed breakfast ordering

Environments:
Local → Staging → Production
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

# ======================================================
# BASE DIRECTORY
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent


# ======================================================
# ENVIRONMENT FLAGS
# ======================================================
ENV = os.getenv("DJANGO_ENV", "development").lower()
DEBUG = os.getenv("DEBUG", "true").lower() == "true"


# ======================================================
# CORE SECURITY
# ======================================================
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "unsafe-dev-secret-key-change-in-production"
)

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,192.168.1.68"
).split(",")


# ======================================================
# OPTIONAL: TWILIO / SMS (OTP)
# ======================================================
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

# Dev-only: return OTP in response for testing
SEND_PLAINTEXT_OTP = os.getenv(
    "SEND_PLAINTEXT_OTP",
    "false"
).lower() == "true"


# ======================================================
# APPLICATION DEFINITION
# ======================================================
INSTALLED_APPS = [

    # --------------------------------------------------
    # DJANGO CORE
    # --------------------------------------------------
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --------------------------------------------------
    # THIRD-PARTY
    # --------------------------------------------------
    "rest_framework",
    "corsheaders",

    # --------------------------------------------------
    # CORE SYSTEM (GLOBAL BOOTSTRAP)
    # --------------------------------------------------
    "core.apps.CoreConfig",

    # --------------------------------------------------
    # DOMAIN / BUSINESS APPS
    # --------------------------------------------------
    "accounts",
    "ingredients.apps.IngredientsConfig",
    "menu.apps.MenuConfig",
    "snacks.apps.SnacksConfig",
    "orders.apps.OrdersConfig",
]



# ======================================================
# MIDDLEWARE
# ======================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================================
# CORS — REACT FRONTEND
# ======================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Production-only explicit origins
if not DEBUG:
    CORS_ALLOWED_ORIGINS = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        ""
    ).split(",")
else:
    CORS_ALLOWED_ORIGINS = []


# ======================================================
# URL / WSGI
# ======================================================
ROOT_URLCONF = "backend.urls"
WSGI_APPLICATION = "backend.wsgi.application"

DEBUG = False

ALLOWED_HOSTS = [
    "swad-backend.onrender.com",
    "swad-of-tamil.vercel.app",
]

CORS_ALLOWED_ORIGINS = [
    "https://swad-of-tamil.vercel.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://swad-of-tamil.vercel.app",
]

# ======================================================
# TEMPLATES (ADMIN ONLY)
# ======================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ======================================================
# DATABASE (POSTGRES DEFAULT)
# ======================================================
DATABASES = {
    "default": {
        "ENGINE": os.getenv(
            "DB_ENGINE",
            "django.db.backends.postgresql"
        ),
        "NAME": os.getenv("DB_NAME", "swad_of_tamil"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


# ======================================================
# PASSWORD VALIDATION
# ======================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ======================================================
# LOCALIZATION
# ======================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# ======================================================
# STATIC & MEDIA
# ======================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================================================
# DJANGO REST FRAMEWORK — API FIRST
# ======================================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}


# ======================================================
# SECURITY HARDENING
# ======================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# ======================================================
# LOGGING
# ======================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "orders": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
