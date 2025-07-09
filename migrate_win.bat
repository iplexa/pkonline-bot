@echo off
set DB_DSN=postgresql+psycopg2://pkonline:pkonline@db:5432/pkonline

echo Applying migration...
docker-compose run --rm -e DB_DSN=%DB_DSN% bot python -m alembic upgrade head

echo Migration completed! 