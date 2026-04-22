@echo off
REM Run the package tests from the project root.
SET PROJECT_ROOT=%~dp0
SET VENV_PY=%PROJECT_ROOT%venv\Scripts\python.exe

IF NOT EXIST "%VENV_PY%" (
  echo Virtual environment Python not found at %VENV_PY%
  echo Create the venv first with: python -m venv venv
  exit /b 1
)

echo Using Python: %VENV_PY%
"%VENV_PY%" -m pytest -q tests
