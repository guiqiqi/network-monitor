@echo off
REM =========================================================
REM install-monitor.bat
REM - If not running as administrator, relaunches itself elevated
REM - Creates "%ProgramFiles%\network-monitor"
REM - Copies monitor.exe from the script folder into the target folder
REM - If any service is already installed that references monitor.exe
REM   (or a service named "network-monitor"), it will be stopped and deleted
REM - Runs: "monitor.exe install --startup auto"
REM - Silent (no pause)
REM =========================================================

REM --- Ensure we are elevated ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Not running as administrator — requesting elevation...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

REM --- Variables ---
set "DEST=%ProgramFiles%\network-monitor"
set "SRC=%~dp0monitor.exe"

REM --- Create destination directory if needed ---
if not exist "%DEST%" (
    mkdir "%DEST%"
    if errorlevel 1 (
        echo Failed to create "%DEST%".
        exit /b 1
    )
)

REM --- Ensure monitor.exe exists next to this script ---
if not exist "%SRC%" (
    echo monitor.exe not found in script directory ("%~dp0").
    exit /b 1
)

REM --- Copy monitor.exe to destination (overwrite if exists) ---
copy /Y "%SRC%" "%DEST%\monitor.exe" >nul
if errorlevel 1 (
    echo Failed to copy monitor.exe to "%DEST%".
    exit /b 1
)

REM --- Function: stop and delete a service (waits for stop) ---
REM Usage: call :StopAndDeleteService ServiceName
:StopAndDeleteService
if "%~1"=="" goto :eof
set "svcname=%~1"
echo Stopping service "%svcname%" if running...
sc query "%svcname%" >nul 2>&1
if %errorlevel% equ 1060 (
    echo Service "%svcname%" not found.
    goto :eof
)
REM Try to stop (ignore errors)
sc stop "%svcname%" >nul 2>&1

REM Wait up to ~30 seconds for service to stop
set /a tries=0
:wait_stop
set /a tries+=1
for /f "tokens=3" %%A in ('sc query "%svcname%" ^| findstr /i "STATE"') do set "state=%%A"
if /I "%state%"=="STOPPED" (
    echo Service "%svcname%" stopped.
) else (
    if %tries% geq 15 (
        echo Timeout waiting for "%svcname%" to stop.
    ) else (
        timeout /t 2 >nul
        goto :wait_stop
    )
)

REM Delete the service (ignore errors)
echo Deleting service "%svcname%"...
sc delete "%svcname%" >nul 2>&1
goto :eof

REM --- Detect existing services referencing monitor.exe via PowerShell/WMI ---
set "FOUND_ANY=0"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command ^
  "Get-WmiObject Win32_Service ^| Where-Object { $_.PathName -and $_.PathName.ToLower().Contains('monitor.exe') } ^| Select-Object -ExpandProperty Name"`) do (
    set "FOUND_ANY=1"
    REM Call function to stop & delete each found service
    call :StopAndDeleteService "%%S"
)

REM --- Also check for a service explicitly named "network-monitor" ---
sc query "network-monitor" >nul 2>&1
if %errorlevel% equ 0 (
    set "FOUND_ANY=1"
    call :StopAndDeleteService "network-monitor"
)

REM If none found, continue with install
if "%FOUND_ANY%"=="1" (
    echo Existing monitor-related service(s) were processed.
)

REM --- Run installer command ---
echo Installing service...
"%DEST%\monitor.exe" install --startup auto
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" (
    echo Install command completed successfully.
) else (
    echo Install command exited with code %RC%.
)

exit /b %RC%
