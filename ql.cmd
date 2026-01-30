@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ql - Quick Log Analysis Tool
:: Usage: ql <log_file> [config_pattern]
:: Examples:
::   ql aaa.log
::   ql aaa.log audio.py
::   ql log\1.log qlcfg\*.py

:: Save original working directory
set "ORIG_DIR=%CD%"
set "SCRIPT_DIR=%~dp0"

:: Check arguments
if "%~1"=="" (
    echo Usage: ql ^<log_file^> [config_pattern]
    echo.
    echo Examples:
    echo   ql aaa.log              Use qlcfg\*.py to analyze log
    echo   ql aaa.log audio.py     Use only audio.py config
    echo   ql log\1.log            Analyze log in log directory
    exit /b 1
)

:: Get absolute path of log file (resolve relative to original directory)
set "LOG_FILE=%~f1"
set "CONFIG_PATTERN=%~2"

:: Determine qlcfg folder location
:: First check parent directory (ql's sibling folder), then check inside ql folder
set "QLCFG_DIR="
if exist "%SCRIPT_DIR%..\qlcfg\" (
    set "QLCFG_DIR=%SCRIPT_DIR%..\qlcfg"
) else if exist "%SCRIPT_DIR%qlcfg\" (
    set "QLCFG_DIR=%SCRIPT_DIR%qlcfg"
) else if exist "%SCRIPT_DIR%configs\" (
    :: Fallback to legacy configs folder
    set "QLCFG_DIR=%SCRIPT_DIR%configs"
)

:: Use default qlcfg\*.py if not specified
if "%CONFIG_PATTERN%"=="" (
    if defined QLCFG_DIR (
        set "CONFIG_PATTERN=!QLCFG_DIR!\*.py"
    ) else (
        echo [ERROR] No qlcfg or configs folder found
        exit /b 1
    )
)

:: Get log file name without path and extension, replace dots with underscores
set "LOG_NAME=%~n1"
set "LOG_NAME=!LOG_NAME:.=_!"

:: Output file paths (in original working directory)
set "OUTPUT_DIR=%ORIG_DIR%\output"
set "JSON_FILE=%OUTPUT_DIR%\%LOG_NAME%.json"
set "HTML_FILE=%OUTPUT_DIR%\%LOG_NAME%.html"

:: Ensure output directory exists
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

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
