#!/bin/sh
set -eu

python manage.py check --deploy --fail-level WARNING
python manage.py collectstatic --noinput
python manage.py verificar_hospedagem
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --config gunicorn.conf.py
