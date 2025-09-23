# #!/bin/bash
# echo "Starting build process..."
# pip install -r requirements.txt

# echo "Running collectstatic..."
# python manage.py collectstatic --noinput

# echo "Static files collected to:"
# ls -la staticfiles_build/static

#!/bin/bash

# Build the project
echo "Building the project..."

# Install project dependencies
python3 -m pip install -r requirements.txt

# Run database migrations
echo "Make Migrations..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# Collect static files
echo "Collect Static..."
python3 manage.py collectstatic --noinput --clear

echo "Build finished successfully."
