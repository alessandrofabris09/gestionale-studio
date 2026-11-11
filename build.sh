#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [ "${RENDER_EXTERNAL_HOSTNAME:-}" = "studio-tecnico-collaudo.onrender.com" ] \
   && [ "${RENDER_GIT_BRANCH:-}" = "collaudo-render" ] \
   && [ "${DJANGO_SETTINGS_MODULE:-}" = "gestionale.settings_staging" ]; then
    python manage.py shell < scripts/collauda_beta_render.py
fi
