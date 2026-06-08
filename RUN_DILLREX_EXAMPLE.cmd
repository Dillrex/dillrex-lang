@echo off
setlocal
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" --version >nul 2>nul
  if %errorlevel% equ 0 (
  ".venv\Scripts\python.exe" -m dillrex run examples\hello.drx
    exit /b %errorlevel%
  )
)

where py >nul 2>nul
if %errorlevel% equ 0 (
  py -m dillrex run examples\hello.drx
) else (
  python -m dillrex run examples\hello.drx
)
