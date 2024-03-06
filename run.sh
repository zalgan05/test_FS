#!/bin/sh
echo "Running migrations..."
python manage.py makemigrations;
python manage.py migrate;

echo "Collecting static files..."
python manage.py collectstatic --noinput;

echo "Starting Celery worker..."
celery -A notification_service worker -l info -P threads &

echo "Starting Celery beat..."
celery -A notification_service beat --loglevel=info &

echo "Copying static files..."
cp -r /app/collected_static/. /backend_static/static/

echo "Starting Gunicorn..."
gunicorn --bind 0:8000 notification_service.wsgi;