#!/bin/sh
set -e

python backend/manage.py migrate --noinput
python backend/manage.py collectstatic --noinput

# Ensure correct import path for the Django project package under backend/
gunicorn --chdir backend stimul_ico.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
