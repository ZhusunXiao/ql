@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ql - Quick Log Analysis Tool
:: Usage: ql <log_file> [config_pattern]
:: Examples:
::   ql aaa.log
::   ql aaa.log audio.py
::   ql log\1.log configs\*.py

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check arguments
if "%~1"=="" (
    echo Usage: ql ^<log_file^> [config_pattern]
    echo.
    echo Examples:
    echo   ql aaa.log              Use configs\*.py to analyze log
    echo   ql aaa.log audio.py     Use only audio.py config
    echo   ql log\1.log            Analyze log in log directory
    exit /b 1
)

set "LOG_FILE=%~1"
set "CONFIG_PATTERN=%~2"

:: Use default configs\*.py if not specified
if "%CONFIG_PATTERN%"=="" (
    set "CONFIG_PATTERN=configs\*.py"
)

:: Get log file name without path and extension
set "LOG_NAME=%~n1"

:: Output file paths
set "JSON_FILE=output\%LOG_NAME%.json"
set "HTML_FILE=output\%LOG_NAME%.html"

:: Ensure output directory exists
if not exist output mkdir output

echo.
echo ========================================
echo   ql - Quick Log
echo ========================================
echo.
echo [LOG]    %LOG_FILE%
echo [CONFIG] %CONFIG_PATTERN%
echo [OUTPUT] %HTML_FILE%
echo.

:: Step 1: Log -> JSON
echo [1/2] Extracting log data...
python "%SCRIPT_DIR%log2json.py" "%LOG_FILE%" %CONFIG_PATTERN% -o "%JSON_FILE%"
if errorlevel 1 (
    echo [ERROR] log2json failed
    exit /b 1
)

:: Step 2: JSON -> HTML
echo.
echo [2/2] Generating HTML...
python "%SCRIPT_DIR%json2html.py" "%JSON_FILE%" "%HTML_FILE%"
if errorlevel 1 (
    echo [ERROR] json2html failed
    exit /b 1
)

echo.
echo ========================================
echo [DONE] %HTML_FILE%
echo ========================================
echo.

:: Auto-open HTML file
start "" "%HTML_FILE%"
