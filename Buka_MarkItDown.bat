@echo off
title Membuka MarkItDown Desktop Studio...
cd /d "%~dp0"

:: Cek keberadaan pythonw.exe
where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw app.py
    exit
)

:: Jika pythonw tidak ditemukan di PATH, gunakan python biasa
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" python app.py
    exit
)

:: Fallback jalur Laragon Python jika PATH belum diset global
if exist "C:\laragon\bin\python\python-3.10\pythonw.exe" (
    start "" "C:\laragon\bin\python\python-3.10\pythonw.exe" app.py
    exit
)

echo [ERROR] Python tidak ditemukan di sistem Anda!
echo Silakan pastikan Python sudah terinstal dan ditambahkan ke PATH.
pause
