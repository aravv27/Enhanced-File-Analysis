@echo off
REM ============================================================
REM AutoSorter — Installation Script
REM 
REM This script:
REM   1. Creates the AppData directory structure
REM   2. Copies application files to AppData\Local\AutoSorter
REM   3. Registers AutoSorter to run on Windows startup
REM   4. Verifies Tesseract OCR is available
REM ============================================================

echo.
echo  ========================================
echo   AutoSorter Installer
echo  ========================================
echo.

SET APP_NAME=AutoSorter
SET INSTALL_DIR=%LOCALAPPDATA%\%APP_NAME%
SET SOURCE_DIR=%~dp0

REM Step 1: Create directories
echo [1/4] Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\src" mkdir "%INSTALL_DIR%\src"
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"
echo       Done: %INSTALL_DIR%

REM Step 2: Copy files
echo [2/4] Copying application files...
xcopy /Y /Q "%SOURCE_DIR%src\*.py" "%INSTALL_DIR%\src\" >nul 2>&1
xcopy /Y /Q "%SOURCE_DIR%config\*.json" "%INSTALL_DIR%\config\" >nul 2>&1
copy /Y "%SOURCE_DIR%requirements.txt" "%INSTALL_DIR%\" >nul 2>&1
echo       Files copied successfully.

REM Step 3: Register for Windows startup
echo [3/4] Registering for Windows startup...
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V "%APP_NAME%" /T REG_SZ /D "pythonw \"%INSTALL_DIR%\src\main.py\"" /F >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo       Startup registration successful.
) else (
    echo       WARNING: Could not add startup registry key.
    echo       You may need to run this script as Administrator.
)

REM Step 4: Check Tesseract
echo [4/4] Checking Tesseract OCR...
where tesseract >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo       Tesseract found on PATH.
) else (
    echo.
    echo       WARNING: Tesseract OCR not found on PATH!
    echo       OCR features (scanned PDFs, images) will not work.
    echo       Install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo       After installing, add the install directory to your PATH.
    echo.
)

echo.
echo  ========================================
echo   Installation Complete!
echo  ========================================
echo.
echo   Install location: %INSTALL_DIR%
echo   Config file:      %INSTALL_DIR%\config\config.json
echo   Categories:       %INSTALL_DIR%\config\categories.json
echo   Logs:             %INSTALL_DIR%\logs\
echo.
echo   AutoSorter will start automatically on next login.
echo   To start now, run:
echo     pythonw "%INSTALL_DIR%\src\main.py"
echo.
echo   To uninstall, run:
echo     REG DELETE "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V "%APP_NAME%" /F
echo     rmdir /S /Q "%INSTALL_DIR%"
echo.
pause
