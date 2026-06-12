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

echo Running Dillrex bootstrap tests...
"%PY%" -m unittest tests.test_bootstrap
if errorlevel 1 exit /b 1

echo.
echo Checking machine-readable bootstrap output modes...
"%PY%" -m dillrex bootstrap\dillrex-self.drx --tokens examples\no_input.drx >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrex-self.drx --ast examples\no_input.drx >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrexc.drx check examples\no_input.drx >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrexc.drx build examples\no_input.drx bootstrap\_verify_no_input.drxc >nul
if errorlevel 1 exit /b 1
if not exist bootstrap\_verify_no_input.drxc exit /b 1
"%PY%" -m dillrex bootstrap\dillrexc.drx read bootstrap\_verify_no_input.drxc >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrexc.drx decode bootstrap\_verify_no_input.drxc >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrexc.drx run-artifact bootstrap\_verify_no_input.drxc >nul
if errorlevel 1 exit /b 1
del bootstrap\_verify_no_input.drxc

echo.
echo Running nested quiet self-host smoke test...
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrex-self.drx --quiet examples\math.drx
if errorlevel 1 exit /b 1

echo.
echo Running Dillrex compiler front-end through self-host chain...
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrexc.drx run examples\no_input.drx
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrexc.drx build examples\math.drx bootstrap\_verify_math.drxc >nul
if errorlevel 1 exit /b 1
if not exist bootstrap\_verify_math.drxc exit /b 1
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrexc.drx read bootstrap\_verify_math.drxc >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrexc.drx decode bootstrap\_verify_math.drxc >nul
if errorlevel 1 exit /b 1
"%PY%" -m dillrex bootstrap\dillrex-self.drx --quiet bootstrap\dillrexc.drx run-artifact bootstrap\_verify_math.drxc >nul
if errorlevel 1 exit /b 1
del bootstrap\_verify_math.drxc

echo.
echo Bootstrap verification OK.
