' Launcher Senyap (Tanpa CMD Pop-up) untuk MarkItDown Desktop Studio
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

' Cari pythonw.exe dari path aktif atau default Laragon
Dim pythonwPath
pythonwPath = "pythonw.exe"

' Jalankan desktop_app.py secara silent (0 = tersembunyi, False = async)
WshShell.Run """" & pythonwPath & """ """ & scriptDir & "\desktop_app.py""", 0, False
