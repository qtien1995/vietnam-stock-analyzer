Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Đường dẫn thư mục hiện tại
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Chạy lệnh cập nhật và mở Dashboard tĩnh trên Microsoft Edge ngầm (0 = No Window)
' Chuẩn kiến trúc Zero-Server: Không chạy web server localhost:5000
WshShell.Run "cmd /c python main.py --mode dashboard", 0, False

