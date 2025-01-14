@echo off
chcp 65001>nul

echo [Step 1] Checking environment...
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [Step 2] Installing PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed
    pause
    exit /b 1
)

echo [Step 3] Cleaning old files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo [Step 4] Checking FFmpeg...
if not exist "ffmpeg" mkdir "ffmpeg"
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

echo [Step 5] Building...
:: Directory mode build - removes --onefile flag and adds --collect-all
pyinstaller --noconfirm --windowed --name "M3U8_to_MP4" ^
    --add-data "ffmpeg/ffmpeg.exe;ffmpeg/" ^
    --add-data "ffmpeg/ffprobe.exe;ffmpeg/" ^
    --hidden-import PyQt6.sip ^
    --hidden-import ffmpeg ^
    --hidden-import requests ^
    --collect-all ffmpeg ^
    --collect-all requests ^
    --clean ^
    gui_converter.py

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

if not exist "dist\M3U8_to_MP4\M3U8_to_MP4.exe" (
    echo [ERROR] Output file not found
    pause
    exit /b 1
)

:: Copy additional files if needed
echo [Step 6] Copying additional files...
copy "requirements.txt" "dist\M3U8_to_MP4\" >nul 2>nul
copy "README.md" "dist\M3U8_to_MP4\" >nul 2>nul

echo [SUCCESS] Build completed. Program folder is in dist\M3U8_to_MP4
echo You can now run the program from dist\M3U8_to_MP4\M3U8_to_MP4.exe
pause
