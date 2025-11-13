@echo off
REM Build script for Data Monitor Windows executable
REM This script creates a single-file .exe using PyInstaller

echo ============================================
echo Data Monitor - Build Script
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

REM Install pywin32 for better Windows integration (optional)
echo.
echo Installing pywin32 for Windows integration...
pip install pywin32
if errorlevel 1 (
    echo WARNING: Failed to install pywin32 - some features may be limited
)

REM Clean previous build artifacts
echo.
echo Cleaning previous build artifacts...
if exist "dist\" rmdir /s /q dist
if exist "build\" rmdir /s /q build

REM Build with PyInstaller using spec file
echo.
echo Building executable with PyInstaller...
pyinstaller packaging\pyinstaller.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

REM Check if executable was created
if not exist "dist\data_monitor.exe" (
    echo ERROR: Executable was not created
    exit /b 1
)

REM Display success message
echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo ============================================
echo.
echo Executable location: dist\data_monitor.exe
echo File size: 
dir dist\data_monitor.exe | find "data_monitor.exe"
echo.
echo To run the application:
echo   dist\data_monitor.exe
echo.
echo For full per-process network statistics, run as Administrator.
echo.

REM Optional: Run tests
echo.
set /p run_tests="Run tests before packaging? (y/n): "
if /i "%run_tests%"=="y" (
    echo.
    echo Running tests...
    pytest tests\ -v
    if errorlevel 1 (
        echo WARNING: Some tests failed
    ) else (
        echo All tests passed!
    )
)

echo.
echo Build process complete!
pause
