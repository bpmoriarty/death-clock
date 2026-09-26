' A Windows entry point that does not depend on .pyw file associations.
' Optional /shortcut creates the desktop shortcut; it does not launch the app.
Option Explicit
Dim shell, files, folder, python, command, result, link, shortcutPath
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)

If WScript.Arguments.Count > 0 Then
    If LCase(WScript.Arguments(0)) = "/shortcut" Then
        shortcutPath = files.BuildPath(shell.SpecialFolders("Desktop"), "Death Clock.lnk")
        Set link = shell.CreateShortcut(shortcutPath)
        link.TargetPath = files.BuildPath(shell.ExpandEnvironmentStrings("%SystemRoot%"), "System32\wscript.exe")
        link.Arguments = "//nologo " & Quote(WScript.ScriptFullName)
        link.WorkingDirectory = folder
        link.Description = "Death Clock - a personal reminder to use time well"
        link.Save
        MsgBox "The Death Clock shortcut is on your desktop.", vbInformation, "Death Clock"
        WScript.Quit 0
    End If
End If

python = files.BuildPath(folder, ".venv\Scripts\python.exe")
If Not files.FileExists(python) Then
    LaunchFailed
End If
shell.CurrentDirectory = folder
command = Quote(python) & " -B " & Quote(files.BuildPath(folder, "run.pyw"))
On Error Resume Next
' Hidden console interpreter provides an exit code even if the base Python is missing.
' run.pyw probes the environment, starts pythonw, then exits; this does not wait
' for the lifetime of the clock.
result = shell.Run(command, 0, True)
If Err.Number <> 0 Then
    Err.Clear
    On Error GoTo 0
    LaunchFailed
End If
On Error GoTo 0
If result <> 0 And result <> 10 Then LaunchFailed
WScript.Quit result

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function

Sub LaunchFailed
    Dim appFolder, logs, logPath, stream
    ' Log only a fixed category; never save process output or profile contents.
    On Error Resume Next
    appFolder = files.BuildPath(shell.ExpandEnvironmentStrings("%LOCALAPPDATA%"), "DeathClock")
    If Not files.FolderExists(appFolder) Then files.CreateFolder appFolder
    logs = files.BuildPath(appFolder, "logs")
    If Not files.FolderExists(logs) Then files.CreateFolder logs
    logPath = files.BuildPath(logs, "bootstrap.log")
    If files.FileExists(logPath) Then
        If files.GetFile(logPath).Size >= 32768 Then files.DeleteFile logPath, True
    End If
    Set stream = files.OpenTextFile(logPath, 8, True)
    stream.WriteLine CStr(Now) & " bootstrap: RuntimeUnavailable"
    stream.Close
    On Error GoTo 0
    MsgBox "Death Clock could not start its project Python environment." & vbCrLf & vbCrLf & _
        "If the clock is running, exit it normally before repairing setup. Follow launch troubleshooting in README.md. " & _
        "Do not delete settings.json. No setup changes were made automatically.", vbExclamation, "Death Clock"
    WScript.Quit 1
End Sub
