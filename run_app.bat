@echo off
title TradeDash Application
echo Welcome to TradeDash!

:: Set the working directory to the batch file location
cd /d "%~dp0"

:: Check if conda is available
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Conda is not installed or not in your PATH.
    echo Please install Anaconda or Miniconda first.
    echo Visit: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

:: Check if the tradedash environment exists
conda env list | findstr /C:"tradedash" >nul
if %errorlevel% neq 0 (
    echo Creating conda environment 'tradedash'...
    conda create -y -n tradedash python=3.8
    if %errorlevel% neq 0 (
        echo Failed to create conda environment.
        pause
        exit /b 1
    )
)

:: Activate conda environment directly using the alternative method
echo Activating conda environment 'tradedash'...
call C:\Users\offic\anaconda3\Scripts\activate.bat tradedash

:: Check if requirements are installed
echo Checking and installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Warning: Some dependencies may not have installed correctly.
        echo The application may not function properly.
        echo Press any key to continue anyway...
        pause >nul
    )
)

:: Run the application
echo Starting TradeDash application...
python -m tradedash.main

set APP_EXIT_CODE=%errorlevel%

:: Cleanup routines
echo Cleaning up resources...

:: Kill any potentially hanging Python processes related to our app
taskkill /F /IM python.exe /FI "WINDOWTITLE eq TradeDash*" >nul 2>nul

:: Clear temporary files
if exist "temp\*.tmp" del /F /Q "temp\*.tmp" >nul 2>nul
if exist "temp\*.cache" del /F /Q "temp\*.cache" >nul 2>nul

:: Free up memory by deactivating conda environment
call conda deactivate

if %APP_EXIT_CODE% neq 0 (
    echo Application exited with error code %APP_EXIT_CODE%
    echo Check error messages above
    pause
) else (
    echo Application closed successfully and resources cleaned up
    pause
) 