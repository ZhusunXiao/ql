@echo off
:: Quick Log - Start Vue Visualization
:: Usage: dev.cmd [json_file]

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "NODE_PATH=C:\Users\Public\abin\node"
set "PATH=%NODE_PATH%;%PATH%"

cd /d "%SCRIPT_DIR%"

:: If argument provided, build URL
set "JSON_FILE=%~1"
if not "%JSON_FILE%"=="" (
    set "URL_PARAM=?file=/output/%JSON_FILE%"
) else (
    set "URL_PARAM="
)

echo ========================================
echo   Quick Log - Vue Visualization
echo ========================================
echo.

:: Check if port is in use
set "PORT=5173"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    set "PORT=5174"
)

:: Check if server is already running
curl -s http://localhost:%PORT% >nul 2>&1
if errorlevel 1 (
    echo Starting dev server on port %PORT%...
    echo.
    
    :: Start server in background
    start /b cmd /c "npm.cmd run dev -- --port %PORT%"
    
    :: Wait for server
    echo Waiting for server to start...
    :wait_loop
    timeout /t 1 /nobreak >nul
    curl -s http://localhost:%PORT% >nul 2>&1
    if errorlevel 1 goto wait_loop
    
    echo Server started!
) else (
    echo Server already running on port %PORT%
)

echo.

:: Open browser
set "URL=http://localhost:%PORT%/%URL_PARAM%"
echo Opening browser: %URL%
start "" "%URL%"

echo.
echo [OK] Browser opened!
echo.
echo Press Ctrl+C to stop the server.

:: Keep window open if we started the server
if errorlevel 0 (
    pause >nul
)

endlocal
