@echo off
echo Stopping PK Online Web Interface...
echo.

docker-compose stop web-backend web-frontend

echo.
echo Web services stopped successfully!
echo.
pause 