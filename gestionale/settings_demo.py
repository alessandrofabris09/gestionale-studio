"""Configurazione del servizio pubblico dedicato alla demo."""
import os
from pathlib import Path
from urllib.parse import urlsplit

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ON_RENDER = os.environ.get('RENDER') == 'true'
PUBLIC_DEPLOY = ON_RENDER or os.environ.get('DEMO_PUBLIC_DEPLOY') == '1'
DEMO_SITE_URL = os.environ.get('DEMO_SITE_URL', 'http://localhost:8000').rstrip('/')
origin = urlsplit(DEMO_SITE_URL)
if not origin.hostname or origin.path or origin.query or origin.fragment or origin.username:
    raise ImproperlyConfigured('DEMO_SITE_URL deve essere un’origine senza percorso.')

SECRET_KEY = os.environ.get('DEMO_SECRET_KEY', 'solo-sviluppo-demo-locale')
DEFAULT_FROM_EMAIL = os.environ.get('DEMO_FROM_EMAIL', 'demo@studiotecnicocloud.it')
resend_key = os.environ.get('DEMO_RESEND_API_KEY', '')
database_url = os.environ.get('DEMO_DATABASE_URL', '')
if PUBLIC_DEPLOY:
    if (
        origin.scheme != 'https' or len(os.environ.get('DEMO_SECRET_KEY', '')) < 50
        or not resend_key or not os.environ.get('DEMO_FROM_EMAIL')
        or not database_url.startswith(('postgres://', 'postgresql://'))
        or database_url == os.environ.get('DATABASE_URL')
    ):
        raise ImproperlyConfigured('Configurare dominio HTTPS, segreto, email e database dedicati alla demo.')

DEBUG = False
ALLOWED_HOSTS = [origin.hostname] if PUBLIC_DEPLOY else ['localhost', '127.0.0.1', 'testserver']
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if ON_RENDER and render_host:
    ALLOWED_HOSTS.append(render_host)
CSRF_TRUSTED_ORIGINS = [DEMO_SITE_URL]
SECURE_SSL_REDIRECT = PUBLIC_DEPLOY
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if ON_RENDER else None
SECURE_HSTS_SECONDS = 31536000 if PUBLIC_DEPLOY else 0
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CSP = {
    'default-src': ["'self'"],
    'object-src': ["'none'"],
    'base-uri': ["'none'"],
    'frame-ancestors': ["'none'"],
    'form-action': ["'self'"],
}
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = PUBLIC_DEPLOY
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 86400

ROOT_URLCONF = 'gestionale.urls_demo'
INSTALLED_APPS = ['django.contrib.staticfiles', 'demo']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]
DATABASES = {'default': (
    dj_database_url.parse(database_url, ssl_require=True)
    if PUBLIC_DEPLOY else {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'demo-local.sqlite3'}
)}
EMAIL_BACKEND = (
    'anymail.backends.resend.EmailBackend' if PUBLIC_DEPLOY
    else 'django.core.mail.backends.console.EmailBackend'
)
ANYMAIL = {'RESEND_API_KEY': resend_key}
EMAIL_TIMEOUT = 8
DEMO_CLEANUP_CRON_TOKEN = os.environ.get('DEMO_CLEANUP_CRON_TOKEN', '')
LANGUAGE_CODE = 'it'
TIME_ZONE = 'Europe/Rome'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles-demo'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': (
        'whitenoise.storage.CompressedManifestStaticFilesStorage' if PUBLIC_DEPLOY
        else 'django.contrib.staticfiles.storage.StaticFilesStorage'
    )},
}
