@echo off
setlocal enabledelayedexpansion

:: Quick Log - Log Analysis Tool
:: Usage: ql <log_file> [config1.py] [config2.py] ...

:: Set paths
set "SCRIPT_DIR=%~dp0"
set "NODE_PATH=C:\Users\Public\abin\node"

:: Get current directory (support UNC paths)
:: Use pushd/popd trick to handle UNC paths
for /f "tokens=*" %%i in ('cd') do set "WORK_DIR=%%i"
:: If current dir is UNC path, %CD% might fail, use log file's directory instead
if "!WORK_DIR!"=="" set "WORK_DIR=%~dp1"
if "!WORK_DIR:~-1!"=="\" set "WORK_DIR=!WORK_DIR:~0,-1!"

:: Add Node.js to PATH
set "PATH=%NODE_PATH%;%PATH%"

:: Check arguments
if "%~1"=="" (
    echo Quick Log - Log Timeline Visualization Tool
    echo.
    echo Usage: ql ^<log_file^> [config1.py] [config2.py] ...
    echo.
    echo Examples:
    echo   ql log/1.log                    - Use qlcfg/*.py configs
    echo   ql log/1.log audio.py           - Use specified config
    echo   ql log/1.log configs/audio.py configs/system.py
    echo.
    exit /b 1
)

:: Get log file name and full path
set "LOG_FILE=%~1"
set "LOG_NAME=%~n1"
set "LOG_FULL=%~f1"
set "LOG_DIR=%~dp1"

:: Set output file path
:: If log file is on a network path, output to log file's directory
:: Otherwise output to current directory
echo !LOG_FULL! | findstr /b "\\\\" >nul
if not errorlevel 1 (
    :: Network path - output to same directory as log file
    set "JSON_FILE=!LOG_DIR!!LOG_NAME!.json"
) else (
    :: Local path - output to current directory
    set "JSON_FILE=!WORK_DIR!\!LOG_NAME!.json"
)

:: Convert JSON_FILE to forward slashes for URL
set "JSON_PATH=!JSON_FILE!"
set "JSON_PATH=!JSON_PATH:\=/!"

:: Build log2json command arguments
set "CONFIG_ARGS="
set "ARGNUM=0"
for %%a in (%*) do (
    set /a ARGNUM+=1
    if !ARGNUM! gtr 1 (
        set "CONFIG_ARGS=!CONFIG_ARGS! %%a"
    )
)

:: If no config files specified, use default qlcfg/*.py
if "%CONFIG_ARGS%"=="" (
    set "CONFIG_ARGS=%SCRIPT_DIR%qlcfg\*.py"
)

echo ========================================
echo   Quick Log - Log Analysis
echo ========================================
echo.

:: Step 1: Run log2json.py
echo [1/2] Analyzing log file...
echo       Log: %LOG_FILE%
echo       Config: %CONFIG_ARGS%
echo.

python "%SCRIPT_DIR%log2json.py" "%LOG_FILE%" %CONFIG_ARGS% -o "%JSON_FILE%"

if errorlevel 1 (
    echo.
    echo [ERROR] Log analysis failed!
    exit /b 1
)

echo.

:: Step 2: Open visualization in browser
echo [2/2] Starting visualization...

:: Check if dist/index.html exists (production build)
if not exist "%SCRIPT_DIR%dist\index.html" goto use_dev_server

echo       Using production build (dist)

:: Check if server is already running
curl -s -m 2 http://localhost:8080 >nul 2>&1
if not errorlevel 1 (
    echo       HTTP server already running on port 8080
    goto open_browser_prod
)

echo       Starting HTTP server on port 8080...
start /b cmd /c "python "%SCRIPT_DIR%serve.py" 8080"
timeout /t 2 /nobreak >nul

:open_browser_prod
set "URL=http://localhost:8080/?file=/file/!JSON_PATH!"
goto open_browser

:use_dev_server
echo       No dist build found, using dev server

set "PORT=5173"
curl -s http://localhost:5173 >nul 2>&1
if not errorlevel 1 goto server_ready

curl -s http://localhost:5174 >nul 2>&1
if not errorlevel 1 (
    set "PORT=5174"
    goto server_ready
)

echo       Starting dev server...
start /b cmd /c "cd /d %SCRIPT_DIR% && npm.cmd run dev"

:wait_server
timeout /t 1 /nobreak >nul
curl -s http://localhost:5173 >nul 2>&1
if not errorlevel 1 goto server_ready
curl -s http://localhost:5174 >nul 2>&1
if not errorlevel 1 (
    set "PORT=5174"
    goto server_ready
)
goto wait_server

:server_ready
set "URL=http://localhost:!PORT!/?file=/file/!JSON_PATH!"

:open_browser
:: Open browser
echo       Opening browser: !URL!
start "" "!URL!"

echo.
echo [OK] Done!
echo.

endlocal
