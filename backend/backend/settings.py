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

# TEMPORARY FIX: Allow all hosts for tunnel testing
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "192.168.1.68",  # Your local IP
    "*",  # Allow all for tunnel testing
]


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
    "django.contrib.sites",

    # --------------------------------------------------
    # THIRD-PARTY
    # --------------------------------------------------
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "dj_rest_auth",

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
# URL CONFIGURATION
# ======================================================
ROOT_URLCONF = "backend.urls"
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

if DEBUG:
    # Development: Allow all localhost ports for Vite + tunnels
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        # Add your tunnel URLs here when using ngrok/localtunnel
        # "https://your-tunnel-url.ngrok.io",
        # "https://your-subdomain.loca.lt",
    ]

    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
    ]
else:
    # Production: Explicit origins only
    CORS_ALLOWED_ORIGINS = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://swad-of-tamil.vercel.app"
    ).split(",")

    CSRF_TRUSTED_ORIGINS = [
        "https://swadoftamil2-0.onrender.com",
        "https://swad-of-tamil.vercel.app",
    ]

# ✔ Allow custom idempotency header + defaults
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-idempotency-key",  # ← Custom header for duplicate prevention
]

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
# DJANGO-ALLAUTH CONFIGURATION
# ======================================================

# Required for allauth
SITE_ID = 1

# Allauth settings for social login
ACCOUNT_EMAIL_VERIFICATION = "none"  # Skip email verification for simplicity
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_EMAIL_REQUIRED = False

# ======================================================
# DATABASE CONFIGURATION
# ======================================================
db_engine = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")
if "postgresql" in db_engine:
    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ======================================================
# AUTHENTICATION
# ======================================================
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

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
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "accounts.firebase_auth.FirebaseAuthentication",  # Disabled for testing
        # "accounts.firebase_auth.FirebaseTokenAuthentication",  # Disabled for testing
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}


# ======================================================
# JWT CONFIGURATION
# ======================================================
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  # 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),     # 7 days
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}


# ======================================================
# SECURITY HARDENING
# ======================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_SSL_REDIRECT = not DEBUG  # ✅ FIX

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax" if DEBUG else "None"

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax" if DEBUG else "None"


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

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


# ======================================================
# FIREBASE CONFIGURATION
# ======================================================
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
}