@echo off
REM Quick test runner for Data Monitor

echo ============================================
echo Data Monitor - Test Runner
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo ERROR: Virtual environment not found
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)

REM Run tests
echo.
echo Running unit tests...
echo ----------------------------------------
pytest tests\ -v --tb=short

if errorlevel 1 (
    echo.
    echo ======================================
    echo TESTS FAILED!
    echo ======================================
    pause
    exit /b 1
) else (
    echo.
    echo ======================================
    echo ALL TESTS PASSED!
    echo ======================================
)

echo.
echo Test Summary:
echo - Database tests: test_db.py
echo - Monitor tests: test_monitor.py  
echo - Recommender tests: test_recommender.py
echo.

pause
