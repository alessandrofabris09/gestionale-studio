"""Impostazioni riservate ai test automatici: SQLite in memoria, servizi esterni spenti."""
import os
from pathlib import Path
from tempfile import mkdtemp

os.environ['PYTHON_DOTENV_DISABLED'] = '1'
os.environ['DATABASE_URL'] = ''
os.environ['USE_BACKBLAZE_B2'] = 'False'
os.environ['RESEND_API_KEY'] = ''
os.environ.pop('RENDER', None)

from .settings import *  # noqa: F403,E402

SECRET_KEY = 'chiave-fittizia-esclusivamente-per-test-automatici'
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:', 'TEST': {'NAME': ':memory:'}}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
USE_BACKBLAZE_B2 = False
STRIPE_SECRET_KEY = ''
STRIPE_PUBLIC_KEY = ''
STRIPE_WEBHOOK_SECRET = ''
STRIPE_PRICE_PRO_MONTHLY = ''
SITE_URL = 'http://testserver'
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
TEST_FILES_DIR = Path(mkdtemp(prefix='studio-tecnico-ci-'))
MEDIA_ROOT = TEST_FILES_DIR / 'media'
STATIC_ROOT = TEST_FILES_DIR / 'staticfiles'
STATIC_ROOT.mkdir()
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
