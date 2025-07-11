@echo off
echo Starting PK Online Web Interface in development mode...
echo.

echo Building and starting development services...
docker-compose --profile dev up -d --build web-backend web-frontend-dev

echo.
echo Development services started successfully!
echo.
echo Web Interface (dev): http://localhost:3001
echo API Documentation: http://localhost:8000/docs
echo.
echo To view logs:
echo   docker-compose logs -f web-backend
echo   docker-compose logs -f web-frontend-dev
echo.
echo To stop services:
echo   docker-compose --profile dev stop web-backend web-frontend-dev
echo.
pause 