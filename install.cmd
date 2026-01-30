@echo off
chcp 65001 >nul 2>&1
echo.
echo ========================================
echo   Quick Log Installation (Windows)
echo ========================================
echo.

set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo Install directory: %INSTALL_DIR%
echo.

:: Check if already in PATH
echo %PATH% | findstr /i /c:"%INSTALL_DIR%" >nul
if %errorlevel%==0 (
    echo [INFO] %INSTALL_DIR% is already in PATH
    goto :done
)

:: Get current user PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"

:: Add to user PATH
if defined USER_PATH (
    setx PATH "%USER_PATH%;%INSTALL_DIR%" >nul
) else (
    setx PATH "%INSTALL_DIR%" >nul
)

if %errorlevel%==0 (
    echo [OK] Added to user PATH
    echo.
    echo Please reopen terminal for PATH to take effect
) else (
    echo [ERROR] Failed to add PATH, please add manually:
    echo   %INSTALL_DIR%
)

:done
echo.
echo ========================================
echo   Usage:
echo   ql ^<log_file^> [config_pattern]
echo ========================================
echo.
pause
