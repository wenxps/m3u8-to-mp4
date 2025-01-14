@echo off
chcp 65001>nul

echo [Step 1] Checking environment...
echo.

:: Check Python environment
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo Python check passed
echo.

echo [Step 2] Installing PyInstaller...
echo.
:: Install PyInstaller
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed
    pause
    exit /b 1
)
echo PyInstaller installation completed
echo.

echo [Step 3] Cleaning old files...
echo.
:: Clean old files
if exist "build" (
    rmdir /s /q "build"
    echo build directory deleted
)
if exist "dist" (
    rmdir /s /q "dist"
    echo dist directory deleted
)
if exist "*.spec" (
    del /q "*.spec"
    echo spec file deleted
)
echo Cleaning completed
echo.

echo [Step 4] Checking FFmpeg...
echo.
:: Check FFmpeg
if not exist "ffmpeg" (
    mkdir "ffmpeg"
    echo ffmpeg directory created
)

if not exist "ffmpeg\ffmpeg.exe" (
    echo [ERROR] ffmpeg.exe not found in ffmpeg folder
    pause
    exit /b 1
)
if not exist "ffmpeg\ffprobe.exe" (
    echo [ERROR] ffprobe.exe not found in ffmpeg folder
    pause
    exit /b 1
)
echo FFmpeg check passed
echo.

echo [Step 5] Building...
echo.
:: Build
echo Running PyInstaller...
pyinstaller --noconfirm --onefile --windowed --name "M3U8_to_MP4" --add-data "ffmpeg/ffmpeg.exe;ffmpeg/" --add-data "ffmpeg/ffprobe.exe;ffmpeg/" --hidden-import PyQt6.sip --hidden-import ffmpeg --hidden-import requests --clean gui_converter.py

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

if not exist "dist\M3U8_to_MP4.exe" (
    echo [ERROR] Output file not found
    pause
    exit /b 1
)

echo [SUCCESS] Build completed. EXE file is in dist folder
echo.
echo Press any key to exit...
pause > nul
