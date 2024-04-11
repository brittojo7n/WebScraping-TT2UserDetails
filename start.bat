@echo off
title Totem Tribe 2 Player Info
cls
cd /d %~dp0

echo.
echo Totem Tribe 2 Player Info
echo Made by: brittojo7n
echo -------------------------
echo 1. Run index.py (Scrape Players)
echo 2. Run server.py (Web Server To View Details)
echo 3. Run sort.py (Sort dataset)
echo 4. Exit
echo.

:menu
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Running index.py...
    python index.py
    pause
    goto menu
) else if "%choice%"=="2" (
    echo Running server.py...
    python server.py
    pause
    goto menu
) else if "%choice%"=="3" (
    echo Running sort.py...
    python sort.py
    pause
    goto menu
) else if "%choice%"=="4" (
    exit
) else (
    echo Invalid choice. Please try again.
    pause
    goto menu
)
