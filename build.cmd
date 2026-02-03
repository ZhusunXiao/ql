@echo off
setlocal

:: Quick Log - Build for Production
:: Usage: build.cmd

set "SCRIPT_DIR=%~dp0"
set "NODE_PATH=C:\Users\Public\abin\node"
set "PATH=%NODE_PATH%;%PATH%"

cd /d "%SCRIPT_DIR%"

echo ========================================
echo   Quick Log - Build
echo ========================================
echo.

echo Building production version...
echo.

call npm.cmd run build

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)

echo.
echo [OK] Build complete!
echo     Output: %SCRIPT_DIR%dist
echo.

endlocal
