#!/bin/sh
set -e

python stimul_ico/manage.py migrate --noinput
python stimul_ico/manage.py collectstatic --noinput

gunicorn stimul_ico.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
