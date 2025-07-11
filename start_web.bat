@echo off
echo Starting PK Online Web Interface with Docker Compose...
echo.

echo Building and starting all services...
docker-compose up -d --build web-backend web-frontend

echo.
echo Services started successfully!
echo.
echo Web Interface: http://localhost:3000
echo API Documentation: http://localhost:8000/docs
echo.
echo To view logs:
echo   docker-compose logs -f web-backend
echo   docker-compose logs -f web-frontend
echo.
echo To stop services:
echo   docker-compose stop web-backend web-frontend
echo.
pause 