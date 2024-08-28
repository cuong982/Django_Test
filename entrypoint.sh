#!/bin/sh

echo "Running entrypoint.sh script..."

if [ "$DB_NAME" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $DB_HOST 5432; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Run Django migrations to ensure the database schema is up-to-date
python manage.py makemigrations
python manage.py migrate

exec "$@"
