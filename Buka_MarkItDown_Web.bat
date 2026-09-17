@echo off
title Menjalankan MarkItDown Web Studio...
cd /d "%~dp0"

echo ========================================================
echo       Memulai Server MarkItDown Web Studio...
echo ========================================================
echo.
echo Server akan aktif di: http://localhost:5000
echo Membuka browser default secara otomatis...
echo.

:: Buka browser secara otomatis setelah 2 detik di background
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:5000'"

:: Jalankan server Flask Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python web_app.py
    goto end
)

if exist "C:\laragon\bin\python\python-3.10\python.exe" (
    "C:\laragon\bin\python\python-3.10\python.exe" web_app.py
    goto end
)

echo [ERROR] Python tidak ditemukan di sistem Anda!
pause

:end
