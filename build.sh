# #!/bin/bash
echo "Starting build process..."
pip install -r requirements.txt

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Static files collected to:"
ls -la staticfiles_build/static




