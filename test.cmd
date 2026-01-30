@echo off
chcp 65001 >nul 2>&1
setlocal

:: Quick Log Self-Test Script (Windows)

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ========================================
echo   Quick Log Self-Test
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed or not in PATH
    exit /b 1
)

:: Run tests
python tests\test_ql.py
set "TEST_RESULT=%errorlevel%"

echo.
if %TEST_RESULT%==0 (
    echo [SUCCESS] All tests passed
) else (
    echo [FAILED] Some tests failed
)

exit /b %TEST_RESULT%
