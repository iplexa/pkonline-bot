@echo off
echo Resetting migration state...
echo This will mark all migrations as applied without actually running them.

set DB_DSN=postgresql+psycopg2://pkonline:pkonline@db:5432/pkonline

docker-compose run --rm -e DB_DSN=%DB_DSN% bot python -m alembic stamp head

echo Migration state reset complete! 