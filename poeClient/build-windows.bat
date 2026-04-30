@echo off
cd /d "%~dp0app"
npm install
npm run dist:win
echo.
echo Build complete. Output: poeClient\app\dist\
