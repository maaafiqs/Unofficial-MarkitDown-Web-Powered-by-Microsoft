@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo   Membuat Shortcut MarkItDown Desktop di Layar Desktop
echo ========================================================

powershell -NoProfile -Command ^
  "$desktop = [Environment]::GetFolderPath('Desktop');" ^
  "$appDir = '%~dp0'.TrimEnd('\');" ^
  "$vbsPath = Join-Path $appDir 'Buka_MarkItDown.vbs';" ^
  "$shortcutPath = Join-Path $desktop 'MarkItDown Desktop.lnk';" ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$s = $ws.CreateShortcut($shortcutPath);" ^
  "$s.TargetPath = 'wscript.exe';" ^
  "$s.Arguments = '\""' + $vbsPath + '\""';" ^
  "$s.WorkingDirectory = $appDir;" ^
  "$s.Description = 'Aplikasi Desktop Microsoft MarkItDown Studio';" ^
  "$s.IconLocation = 'shell32.dll,70';" ^
  "$s.Save();" ^
  "Write-Host 'Shortcut berhasil dibuat di Desktop!' -ForegroundColor Green"

echo.
echo Selesai! Sekarang Anda bisa membuka MarkItDown langsung dari icon di Desktop.
echo.
pause
