Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Đường dẫn thư mục hiện tại
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Khởi động Flask app ngầm bằng pythonw hoặc python ẩn hoàn toàn (0 = No Window)
WshShell.Run "cmd /c python app.py", 0, False

' Đợi 1.5 giây để server sẵn sàng
WScript.Sleep 1500

' Mở thẳng Microsoft Edge vào trang chủ
WshShell.Run "start msedge http://localhost:5000", 0, False
