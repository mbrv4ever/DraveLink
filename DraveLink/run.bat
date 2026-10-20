@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title DraveLink starten...

REM ---- Python zoeken (3.13 t/m 3.10, anders 'python') ----
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
    echo Python is niet gevonden. Installeer Python 3.10+ van https://www.python.org
    pause
    exit /b 1
)

REM ---- venv maken indien nodig ----
if not exist ".venv\Scripts\python.exe" (
    echo Eenmalige installatie... even geduld.
    %PYEXE% -m venv .venv
)

set "VPY=.venv\Scripts\python.exe"
set "VPYW=.venv\Scripts\pythonw.exe"

REM ---- pakketten controleren/installeren ----
"%VPY%" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Onderdelen installeren...
    "%VPY%" -m pip install --upgrade pip >nul 2>&1
    "%VPY%" -m pip install -r requirements.txt --only-binary=:all:
    if errorlevel 1 (
        echo Installatie mislukt. Probeer herstel.bat
        pause
        exit /b 1
    )
)

REM ---- starten zonder zwart venster ----
start "" "%VPYW%" dravelink.py
exit /b 0
