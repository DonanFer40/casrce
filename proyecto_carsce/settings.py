"""
Django settings for proyecto_carsce project.
Configuración editable directamente desde este archivo.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------
# SEGURIDAD GENERAL
# ---------------------------------------------------------------------

# Ajusta estos valores directamente según tu entorno.
DEBUG = True

# Sustituye este valor por una clave larga, aleatoria y privada.
# No publiques este archivo con una SECRET_KEY real.
SECRET_KEY = "gzr28!#=8$5%0$t(dvbrt3r%q_068$08fg@6x#tb(e6=1ap+kz"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    # "tudominio.com",
]

CSRF_TRUSTED_ORIGINS = [
    # "https://tudominio.com",
]


# ---------------------------------------------------------------------
# APLICACIONES
# ---------------------------------------------------------------------

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inicio_sesion",
    "notas_academicas",
    "gestion_institucional",
    "documentos",
    "bitacora",
]


JAZZMIN_SETTINGS = {
    "site_title": "CASRCE",
    "site_brand": "CASRCE",
    "site_header": "Sistema Administrativo",
    "icons": {
        "inicio_sesion.Usuario": "fas fa-user",
        "inicio_sesion.Nucleos": "fas fa-university",
        "inicio_sesion.Perfiles": "fas fa-id-card",
        "inicio_sesion.PNF": "fas fa-graduation-cap",
        "inicio_sesion.PNFNucleo": "fas fa-project-diagram",
        "inicio_sesion.GacetaOficial": "fas fa-file-alt",
        "inicio_sesion.Cuenta": "fas fa-user-lock",
        "auth.User": "fas fa-user-shield",
        "auth.Group": "fas fa-users",
    },
}


# ---------------------------------------------------------------------
# MIDDLEWARE
# La sesión de cada pestaña se selecciona antes de que otros middlewares
# lean o modifiquen request.session.
# ---------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "middleware.sesiones_por_pestana.SesionesPorPestanaMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Protección de la puerta administrativa CASRCE.
    "middleware.seguridad_admin.SeguridadAdminMiddleware",

    # Control de acceso a las vistas según los roles del usuario.
    "middleware.seguridad_roles.SeguridadRolesMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ---------------------------------------------------------------------
# URLS Y PLANTILLAS
# ---------------------------------------------------------------------

ROOT_URLCONF = "proyecto_carsce.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "inicio_sesion.views.detalles.obtencion_rol.datos_usuario_global",
            ],
        },
    },
]

WSGI_APPLICATION = "proyecto_carsce.wsgi.application"


# ---------------------------------------------------------------------
# BASE DE DATOS
# Modifica estos valores directamente según tu instalación.
# ---------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "casrce",
        "USER": "postgres",
        "PASSWORD": "31438140",
        "HOST": "localhost",
        "PORT": "5432",
        "CONN_MAX_AGE": 60,
    }
}

# Para usar SQLite en desarrollo, sustituye el bloque anterior por:
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }


# ---------------------------------------------------------------------
# VALIDACIÓN DE CONTRASEÑAS
# ---------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ---------------------------------------------------------------------
# INTERNACIONALIZACIÓN
# ---------------------------------------------------------------------

LANGUAGE_CODE = "es-VE"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------
# ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# ---------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"


# ---------------------------------------------------------------------
# GOOGLE GEMINI
# ---------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


# ---------------------------------------------------------------------
# SEGURIDAD ADMINISTRATIVA CASRCE
# Las credenciales se reciben desde la terminal.
# ---------------------------------------------------------------------
from pathlib import Path
import os

CASRCE_ADMIN_USERNAME = os.environ.get("CASRCE_ADMIN_USERNAME")

CASRCE_ADMIN_FERNET_KEY = os.environ.get("CASRCE_ADMIN_FERNET_KEY")

CASRCE_ADMIN_GATE_USERNAME = os.environ.get("CASRCE_ADMIN_GATE_USERNAME")

CASRCE_ADMIN_GATE_PASSWORD_HASH = os.environ.get(
    "CASRCE_ADMIN_GATE_PASSWORD_HASH"
)

# Ruta a la que se redirige cuando no existe autorización administrativa.
CASRCE_ADMIN_LOGIN_URL = "/inicio_sesion/"


# ---------------------------------------------------------------------
# CORREO ELECTRÓNICO
# Configuración SMTP editable directamente.
# Para Gmail, utiliza una contraseña de aplicación, no la contraseña normal.
# ---------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = "uptjfr2025@gmail.com"
EMAIL_HOST_PASSWORD = "mgrt npjf olsw mjev"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 20


# ---------------------------------------------------------------------
# SEGURIDAD DE SESIONES Y COOKIES
# ---------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Se deja False para compatibilidad con el JavaScript existente que lee
# csrftoken para enviar peticiones fetch/AJAX con X-CSRFToken.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# En desarrollo local normalmente DEBUG=True y no se fuerza HTTPS.
# Cuando publiques el sistema bajo HTTPS, ajusta estos valores.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Activa HSTS únicamente cuando el sitio funcione correctamente con HTTPS.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Si tu servidor está detrás de un proxy HTTPS, configura este encabezado
# solo cuando conozcas y controles la configuración del proxy.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ---------------------------------------------------------------------
# VALORES PREDETERMINADOS
# ---------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
