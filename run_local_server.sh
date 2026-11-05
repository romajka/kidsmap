#!/bin/bash
# Local development server. DEBUG is off by default in settings, so enable it here.
source .venv/bin/activate
export DJANGO_DEBUG="${DJANGO_DEBUG:-1}"
python manage.py runserver 0.0.0.0:8000
