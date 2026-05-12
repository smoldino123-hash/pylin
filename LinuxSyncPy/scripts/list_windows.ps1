# List processes with an empty window title
Get-Process | Where-Object { $_.MainWindowTitle -ne $null -and $_.MainWindowTitle -eq '' } | Select-Object Id,ProcessName,StartTime,MainWindowTitle | Format-List
Write-Output '---'
# Show cmd.exe processes
Get-Process -Name cmd -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime,MainWindowTitle | Format-List
Write-Output '---'
# WMIC command line for cmd.exe
wmic process where "name='cmd.exe'" get ProcessId,ParentProcessId,CommandLine /FORMAT:LIST
