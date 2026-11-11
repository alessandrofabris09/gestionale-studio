"""Configurazione esplicita per il collaudo online."""
import os
import re
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def valore_staging(nome):
    return os.environ.get(f'STAGING_{nome}', '').strip()


host = valore_staging('HOST').lower()
if not re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+', host) or host in {
    'gestionale-studio-ti32.onrender.com', 'app.studiotecnicocloud.it',
    'studiotecnicocloud.it', 'www.studiotecnicocloud.it',
}:
    raise ImproperlyConfigured('STAGING_HOST deve indicare il dominio dedicato al collaudo.')

database_url = valore_staging('DATABASE_URL')
database = urlsplit(database_url)
if database.scheme not in {'postgres', 'postgresql'} or not database.hostname or len(database.path) < 2:
    raise ImproperlyConfigured('Configurare STAGING_DATABASE_URL con il database PostgreSQL di collaudo.')

secret_key = valore_staging('SECRET_KEY')
if len(secret_key) < 50 or secret_key.startswith('django-insecure-'):
    raise ImproperlyConfigured('Configurare una STAGING_SECRET_KEY dedicata di almeno 50 caratteri.')

stripe_secret = valore_staging('STRIPE_SECRET_KEY')
stripe_public = valore_staging('STRIPE_PUBLIC_KEY')
if (stripe_secret and not stripe_secret.startswith(('sk_test_', 'rk_test_'))) or (
    stripe_public and not stripe_public.startswith('pk_test_')
):
    raise ImproperlyConfigured('Usare esclusivamente chiavi Stripe di test per lo staging.')

if valore_staging('USE_BACKBLAZE_B2') == 'True' and not all(
    valore_staging(nome) for nome in (
        'B2_APPLICATION_KEY_ID', 'B2_APPLICATION_KEY', 'B2_BUCKET_NAME',
        'B2_REGION_NAME', 'B2_ENDPOINT_URL',
    )
):
    raise ImproperlyConfigured('Configurare tutte le impostazioni del bucket B2 di collaudo.')

os.environ.update({
    'PYTHON_DOTENV_DISABLED': '1',
    'DEBUG': 'False',
    'DATABASE_URL': database_url,
    'SECRET_KEY': secret_key,
    'SITE_URL': f'https://{host}',
    'STRIPE_SECRET_KEY': stripe_secret,
    'STRIPE_PUBLIC_KEY': stripe_public,
})
for nome in (
    'USE_BACKBLAZE_B2', 'B2_APPLICATION_KEY_ID', 'B2_APPLICATION_KEY',
    'B2_BUCKET_NAME', 'B2_REGION_NAME', 'B2_ENDPOINT_URL',
    'RESEND_API_KEY', 'EMAIL_FROM_NOTIFICHE', 'ALERT_EMAIL',
    'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 'EMAIL_USE_SSL',
    'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD',
    'STRIPE_WEBHOOK_SECRET', 'STRIPE_PRICE_PRO_MONTHLY', 'STRIPE_COUPON_PRO_FIRST_YEAR',
    'STRIPE_AUTOMATIC_TAX',
    'CODICE_CRON_AGENDA', 'CODICE_CRON_ALERT', 'CODICE_ICS_AGENDA', 'BETA_REMINDER_CRON_TOKEN',
):
    valore = valore_staging(nome)
    if valore:
        os.environ[nome] = valore
    else:
        os.environ.pop(nome, None)

from .settings import *  # noqa: E402,F403

ALLOWED_HOSTS = [host]
CSRF_TRUSTED_ORIGINS = [SITE_URL]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Durata breve durante il collaudo. Gunicorn riconosce HTTPS dal proxy Render.
SECURE_HSTS_SECONDS = 300
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    if valore_staging('RESEND_API_KEY') and valore_staging('EMAIL_FROM_NOTIFICHE'):
        EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
        ANYMAIL = {'RESEND_API_KEY': valore_staging('RESEND_API_KEY')}
        DEFAULT_FROM_EMAIL = EMAIL_FROM_NOTIFICHE
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
