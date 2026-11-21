Set WshShell = CreateObject("WScript.Shell")
strCurDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurDir
strPython = "C:\Users\bhupp\AppData\Local\Programs\Python\Python312\pythonw.exe"
If Not CreateObject("Scripting.FileSystemObject").FileExists(strPython) Then
    strPython = "pythonw.exe"
End If
WshShell.Run """" & strPython & """ desktop_app.py", 0, False
