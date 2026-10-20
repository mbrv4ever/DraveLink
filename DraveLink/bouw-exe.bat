@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title DraveLink .exe bouwen

set "PYEXE="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined PYEXE (
        py -%%V -c "import sys" >nul 2>&1 && set "PYEXE=py -%%V"
    )
)
if not defined PYEXE (
    python -c "import sys" >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
    echo Python niet gevonden. Installeer Python 3.10+ van https://www.python.org
    pause & exit /b 1
)

if not exist ".build-venv\Scripts\python.exe" (
    echo Bouw-omgeving maken...
    %PYEXE% -m venv .build-venv
)
set "BPY=.build-venv\Scripts\python.exe"
"%BPY%" -m pip install --upgrade pip >nul 2>&1
"%BPY%" -m pip install -r requirements.txt pyinstaller Pillow --only-binary=:all:
if errorlevel 1 ( echo Installatie mislukt. & pause & exit /b 1 )

echo Icoon maken...
"%BPY%" maak_icoon.py

echo .exe bouwen (onefile)...
"%BPY%" -m PyInstaller --noconfirm --clean dravelink.spec
if errorlevel 1 ( echo Bouwen mislukt. & pause & exit /b 1 )

echo.
echo Klaar! De .exe staat in de map: dist\DraveLink.exe
echo (Eenmalig portable bestand; je kunt 'm overal neerzetten.)
pause
