pip install -r requirements.txt
python manage.py collectstatic --noinput
gunicorn LOGTRACK.wsgi --log-file -