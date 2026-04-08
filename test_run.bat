@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

pytest
set EXIT_CODE=%ERRORLEVEL%
echo.
echo Test run finished with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
