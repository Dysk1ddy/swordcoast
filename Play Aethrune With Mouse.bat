@echo off
setlocal

REM Always run from this file's folder so the user never needs to cd first.
cd /d "%~dp0"

set "PYTHON_CMD="
set "PYTHON_ARGS="

where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py"
        set "PYTHON_ARGS=-3.13"
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[:2] <= (3, 13) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo The mouse-clickable window needs Python 3.13 because Kivy does not support Python 3.14 yet.
    echo.
    echo Install Python 3.13 from https://www.python.org/downloads/release/python-3130/
    echo and keep Python 3.14 installed for everything else.
    echo.
    echo After installing, run:
    echo     py -3.13 -m pip install -r requirements-gui.txt
    echo     py -3.13 main.py --gui
    echo.
    pause
    exit /b 1
)

"%PYTHON_CMD%" %PYTHON_ARGS% -c "import kivy" >nul 2>nul
if errorlevel 1 (
    echo Kivy is not installed for Python 3.13 yet.
    echo.
    echo Install it with:
    echo     py -3.13 -m pip install -r requirements-gui.txt
    echo.
    pause
    exit /b 1
)

"%PYTHON_CMD%" %PYTHON_ARGS% main.py --gui
set "GAME_EXIT_CODE=%ERRORLEVEL%"

if not "%GAME_EXIT_CODE%"=="0" (
    echo.
    echo The mouse-clickable window closed with an error.
    echo If this is your first time running it, install Kivy for Python 3.13 with:
    echo     py -3.13 -m pip install -r requirements-gui.txt
    echo.
    pause
)

exit /b %GAME_EXIT_CODE%
