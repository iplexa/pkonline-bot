#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Applying database migrations..."
python -m alembic upgrade head || {
    echo "Migration failed, but continuing..."
}

echo "Starting bot..."
python bot.py 