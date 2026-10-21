@echo off
cd /d "%~dp0"
title DraveLink herstellen
echo Dit verwijdert de installatie-omgeving (.venv) en bouwt 'm opnieuw op.
echo Je instellingen en ontvangen bestanden blijven staan.
echo.
pause
if exist ".venv" rmdir /s /q ".venv"
echo Klaar. Start DraveLink nu met run.bat
pause
