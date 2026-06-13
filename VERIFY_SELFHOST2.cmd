@echo off
setlocal

set "PY="

where python >nul 2>nul
if not errorlevel 1 set "PY=python"

if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set "PY=py"
)

if not defined PY (
    if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
        set "PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    )
)

if not defined PY (
    echo Could not find Python. Install Python 3.10+ or run this from Codex.
    exit /b 1
)

echo Building first Dillrex compiler artifact...
"%PY%" -m dillrex bootstrap\dillrexc.drx build bootstrap\dillrexc.drx bootstrap\_selfhost_compiler1.drxc
if errorlevel 1 exit /b 1

echo.
echo Using the self-built compiler artifact to rebuild Dillrex...
"%PY%" -m dillrex bootstrap\dillrexc.drx run-artifact bootstrap\_selfhost_compiler1.drxc build bootstrap\dillrexc.drx bootstrap\_selfhost_compiler2.drxc
if errorlevel 1 exit /b 1

echo.
echo Verifying second-generation compiler artifact...
"%PY%" -m dillrex bootstrap\dillrexc.drx verify bootstrap\_selfhost_compiler2.drxc
if errorlevel 1 exit /b 1

del bootstrap\_selfhost_compiler1.drxc
del bootstrap\_selfhost_compiler2.drxc

echo.
echo Deep self-host verification OK.
