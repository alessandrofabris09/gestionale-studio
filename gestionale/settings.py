from dotenv import load_dotenv
load_dotenv()

import os
import dj_database_url

from pathlib import Path


# =========================
# BASE DIR
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# SICUREZZA
# =========================

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-dev-key'
)

DEBUG = os.environ.get(
    'DEBUG',
    'True'
) == 'True'


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'gestionale-studio-ti32.onrender.com',
    'app.studiotecnicocloud.it',
]


CSRF_TRUSTED_ORIGINS = [
    'https://gestionale-studio-ti32.onrender.com',
    'https://app.studiotecnicocloud.it',
]


# =========================
# APPLICAZIONI
# =========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Storage S3 / Backblaze B2
    'storages',

    # App progetto
    'clienti',
    'immobili',
    'pratiche',
    'scadenze',
    'dashboard',
    'documenti',
    'parcelle',
    'accounts',
    'attivita',
    'agenda',
    'workflow',
    'studi',
    'utenti',
    'landing',
    'billing',
    'backups',
]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================
# URL / WSGI
# =========================

ROOT_URLCONF = 'gestionale.urls'

WSGI_APPLICATION = 'gestionale.wsgi.application'


# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# =========================
# DATABASE
# =========================

DATABASE_URL = os.environ.get(
    'DATABASE_URL'
)


if DATABASE_URL:

    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600
        )
    }

else:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================
# LINGUA / TIMEZONE
# =========================

LANGUAGE_CODE = 'it-it'

TIME_ZONE = 'Europe/Rome'

USE_I18N = True

USE_TZ = True


# =========================
# STATIC FILES
# =========================

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# =========================
# MEDIA / FILE LOCALI
# =========================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# =========================
# STORAGE FILE
# =========================

USE_BACKBLAZE_B2 = os.environ.get(
    'USE_BACKBLAZE_B2',
    'False'
) == 'True'


if USE_BACKBLAZE_B2:

    AWS_ACCESS_KEY_ID = os.environ.get(
        'B2_APPLICATION_KEY_ID'
    )

    AWS_SECRET_ACCESS_KEY = os.environ.get(
        'B2_APPLICATION_KEY'
    )

    AWS_STORAGE_BUCKET_NAME = os.environ.get(
        'B2_BUCKET_NAME'
    )

    AWS_S3_REGION_NAME = os.environ.get(
        'B2_REGION_NAME'
    )

    AWS_S3_ENDPOINT_URL = os.environ.get(
        'B2_ENDPOINT_URL'
    )

    AWS_DEFAULT_ACL = None

    AWS_QUERYSTRING_AUTH = True

    AWS_S3_FILE_OVERWRITE = False

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

else:

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }


# =========================
# LOGIN / LOGOUT
# =========================

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/dashboard/'

LOGOUT_REDIRECT_URL = '/'


# =========================
# EMAIL SMTP TECNICA
# =========================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get(
    'EMAIL_HOST',
    'smtp.gmail.com'
)

EMAIL_PORT = int(
    os.environ.get(
        'EMAIL_PORT',
        465
    )
)

EMAIL_USE_TLS = os.environ.get(
    'EMAIL_USE_TLS',
    'False'
) == 'True'

EMAIL_USE_SSL = os.environ.get(
    'EMAIL_USE_SSL',
    'True'
) == 'True'

EMAIL_HOST_USER = os.environ.get(
    'EMAIL_HOST_USER',
    ''
)

EMAIL_HOST_PASSWORD = os.environ.get(
    'EMAIL_HOST_PASSWORD',
    ''
)

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ALERT_EMAIL = os.environ.get(
    'ALERT_EMAIL'
)


# =========================
# RESEND / EMAIL NOTIFICHE
# =========================

EMAIL_FROM_NOTIFICHE = os.environ.get(
    'EMAIL_FROM_NOTIFICHE',
    'Gestionale Studio <onboarding@resend.dev>'
)


# =========================
# STRIPE
# =========================

STRIPE_SECRET_KEY = os.environ.get(
    'STRIPE_SECRET_KEY',
    ''
)

STRIPE_PUBLIC_KEY = os.environ.get(
    'STRIPE_PUBLIC_KEY',
    ''
)

STRIPE_WEBHOOK_SECRET = os.environ.get(
    'STRIPE_WEBHOOK_SECRET',
    ''
)

STRIPE_PRICE_PRO_MONTHLY = os.environ.get(
    'STRIPE_PRICE_PRO_MONTHLY',
    ''
)


# =========================
# URL SITO
# =========================

SITE_URL = os.environ.get(
    'SITE_URL',
    'https://app.studiotecnicocloud.it'
)