#!/bin/sh
export DB_DSN="postgresql+psycopg2://postgres:yourpassword@db:5432/yourdb"

echo "Creating migration..."
docker-compose run --rm -e DB_DSN="$DB_DSN" bot alembic revision --autogenerate -m "manual migration"

echo "Applying migration..."
docker-compose run --rm -e DB_DSN="$DB_DSN" bot alembic upgrade head 