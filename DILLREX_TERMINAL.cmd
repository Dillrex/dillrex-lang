@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" --version >nul 2>nul
  if %errorlevel% equ 0 (
  ".venv\Scripts\python.exe" -m dillrex shell
    exit /b %errorlevel%
  )
)

where py >nul 2>nul
if %errorlevel% equ 0 (
  py -m dillrex shell
) else (
  python -m dillrex shell
)
