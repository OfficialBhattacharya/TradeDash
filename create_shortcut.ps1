$WshShell = New-Object -ComObject WScript.Shell
$currentDirectory = (Get-Item -Path ".").FullName
$batchFilePath = Join-Path -Path $currentDirectory -ChildPath "run_app.bat"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path -Path $desktopPath -ChildPath "TradeDash.lnk"

# Create the shortcut
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $batchFilePath
$Shortcut.WorkingDirectory = $currentDirectory
$Shortcut.Description = "Launch TradeDash Application"
$Shortcut.IconLocation = "shell32.dll,22" # Default chart icon from Windows
$Shortcut.Save()

Write-Host "Desktop shortcut created at: $shortcutPath" 