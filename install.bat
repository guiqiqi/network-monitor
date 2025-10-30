@echo off
:: This script requires Administrator privileges to run properly.
:: It will request elevation if not already running as Administrator.

:: Check for Administrator rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator privileges confirmed.
) else (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Create the installation directory
set "INSTALL_DIR=C:\Program Files\network-monitor"
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo Created directory: %INSTALL_DIR%
) else (
    echo Directory already exists: %INSTALL_DIR%
)

:: Check if the network-monitor service exists
sc query network-monitor >nul 2>&1
if %errorLevel% == 0 (
    echo Service 'network-monitor' found. Stopping and deleting...
    sc stop network-monitor
    sc delete network-monitor
    echo Service stopped and deleted.
) else (
    echo Service 'network-monitor' not found.
)

:: Copy the executable to the installation directory
set "SOURCE_EXE=.\monitor.exe"
set "TARGET_EXE=%INSTALL_DIR%\monitor.exe"
if exist "%SOURCE_EXE%" (
    copy "%SOURCE_EXE%" "%TARGET_EXE%" /Y
    echo Copied %SOURCE_EXE% to %TARGET_EXE%
) else (
    echo Error: %SOURCE_EXE% not found in current directory.
    pause
    exit /b 1
)

:: Install the service with auto-startup
echo Installing service...
"%TARGET_EXE%" --startup auto install
if %errorLevel% == 0 (
    echo Service installed successfully.
) else (
    echo Failed to install service.
    pause
    exit /b 1
)

:: Start the service
echo Starting the network-monitor service...
sc start network-monitor
if %errorLevel% == 0 (
    echo Service started successfully.
) else (
    echo Failed to start service. Error code: %errorLevel%
)

echo.
echo Installation and service startup completed.
pause