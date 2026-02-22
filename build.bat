@echo off
REM JobTrack — Windows Build Script
REM Packages the app into a standalone .exe using PyInstaller.
REM Run from the project root: build.bat

echo ==========================================
echo  JobTrack — Building Windows Executable
echo ==========================================

REM Ensure PyInstaller is available
pip show pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] PyInstaller not found. Run: pip install pyinstaller
    pause
    exit /b 1
)

REM Clean previous build artifacts
echo [1/3] Cleaning previous build...
IF EXIST build rmdir /s /q build
IF EXIST dist rmdir /s /q dist
IF EXIST JobTrack.spec del JobTrack.spec

REM Run PyInstaller
echo [2/3] Running PyInstaller...
pyinstaller ^
    --name "JobTrack" ^
    --onefile ^
    --windowed ^
    --add-data "assets;assets" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "folium" ^
    --hidden-import "keyring.backends.Windows" ^
    --hidden-import "ui.wizard.base_step" ^
    --hidden-import "ui.wizard.step_api_keys" ^
    --hidden-import "ui.wizard.step_complete" ^
    --hidden-import "ui.wizard.step_google" ^
    --hidden-import "ui.wizard.step_linkedin_reminder" ^
    --hidden-import "ui.wizard.step_location" ^
    --hidden-import "ui.wizard.step_preferences" ^
    --hidden-import "ui.wizard.step_providers" ^
    --hidden-import "ui.wizard.step_tracker" ^
    --hidden-import "ui.wizard.step_welcome" ^
    --hidden-import "ui.wizard.wizard_controller" ^
    main.py

IF ERRORLEVEL 1 (
    echo [ERROR] PyInstaller failed. See output above.
    pause
    exit /b 1
)

echo [3/3] Build complete!
echo Output: dist\JobTrack.exe
echo ==========================================
pause
