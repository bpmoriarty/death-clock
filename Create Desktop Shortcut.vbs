Option Explicit
Dim shell, files, script, host
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
script = files.BuildPath(files.GetParentFolderName(WScript.ScriptFullName), "Start Death Clock.vbs")
host = files.BuildPath(shell.ExpandEnvironmentStrings("%SystemRoot%"), "System32\wscript.exe")
shell.Run Chr(34) & host & Chr(34) & " //nologo " & Chr(34) & script & Chr(34) & " /shortcut", 0, False
