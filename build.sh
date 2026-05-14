#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

echo "===== CURRENT FOLDER ====="
pwd

echo "===== PROJECT FILES ====="
ls -la

echo "===== STATIC FOLDER ====="
ls -la static || echo "No static folder found"

echo "===== STATIC CSS FOLDER ====="
ls -la static/css || echo "No static/css folder found"

echo "===== DJANGO FINDSTATIC ====="
python manage.py findstatic css/style.css --verbosity 2 || echo "findstatic failed"

echo "===== COLLECTSTATIC ====="
python manage.py collectstatic --no-input --clear --verbosity 2

echo "===== COLLECTED STATICFILES ====="
ls -la staticfiles || echo "No staticfiles folder found"

echo "===== COLLECTED CSS ====="
ls -la staticfiles/css || echo "No staticfiles/css folder found"

python manage.py migrate

echo "===== CREATE SUPERUSER IF CONFIGURED ====="
python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); username = os.environ.get('DJANGO_SUPERUSER_USERNAME'); email = os.environ.get('DJANGO_SUPERUSER_EMAIL'); password = os.environ.get('DJANGO_SUPERUSER_PASSWORD'); username and email and password and (User.objects.filter(username=username).exists() or User.objects.create_superuser(username, email, password))"
