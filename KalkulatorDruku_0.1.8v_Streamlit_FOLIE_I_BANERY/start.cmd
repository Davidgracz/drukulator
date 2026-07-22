@echo off
setlocal
cd /d "%~dp0"

py -3.8 --version >nul 2>&1
if not errorlevel 1 goto use_py38

py --version >nul 2>&1
if not errorlevel 1 goto use_py

python --version >nul 2>&1
if not errorlevel 1 goto use_python

echo.
echo Python was not found.
echo Install Python and select "Add Python to PATH" during installation.
pause
exit /b 1

:use_py38
set "PYTHON_CMD=py -3.8"
goto run

:use_py
set "PYTHON_CMD=py"
goto run

:use_python
set "PYTHON_CMD=python"
goto run

:run
echo Python interpreter:
%PYTHON_CMD% --version

echo.
echo Installing required packages...
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo Starting Kalkulator Druku...
%PYTHON_CMD% -m streamlit run app.py
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo The application could not be started.
echo Check the messages shown above.
pause
exit /b 1
