import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = Path(os.getenv("GOCARGO_ENV_FILE", str(BASE_DIR / ".env")))
load_dotenv(ENV_FILE, override=False)
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Define DJANGO_SECRET_KEY en .env o en el entorno.")
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.branches.apps.BranchesConfig",
    "apps.shipments.apps.ShipmentsConfig",
]
MIDDLEWARE = [
    "core.presentation.middleware.ApiErrorContractMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.sqlite3")
if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {"ENGINE": DB_ENGINE, "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3")}
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.getenv("DB_NAME", "gocargo"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }
    if DB_ENGINE == "mssql":
        DATABASES["default"]["OPTIONS"] = {
            "driver": os.getenv("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
        }
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Managua"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
COUNTRIES_API_URL = os.getenv("COUNTRIES_API_URL", "https://countries.trevorblades.com/graphql")
COUNTRIES_CONNECT_TIMEOUT = float(os.getenv("COUNTRIES_CONNECT_TIMEOUT", "3"))
COUNTRIES_READ_TIMEOUT = float(os.getenv("COUNTRIES_READ_TIMEOUT", "5"))
if COUNTRIES_CONNECT_TIMEOUT <= 0 or COUNTRIES_READ_TIMEOUT <= 0:
    raise ImproperlyConfigured("Los tiempos de espera deben ser positivos.")
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "GoCargo API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Demo modular. Acceso publico; autenticacion futura documentada.",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
