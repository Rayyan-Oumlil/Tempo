# Registers the Tempo daily routine in Windows Task Scheduler (current user, only while logged in, local time = ET).
# Usage (PowerShell):  powershell -ExecutionPolicy Bypass -File tools\sched\register.ps1
# Remove again:        powershell -ExecutionPolicy Bypass -File tools\sched\register.ps1 -Remove
# Every job is idempotent (see tempo/sched.py), so the repeated triggers are retries, not double runs.
param([switch]$Remove)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$names = "Tempo-Morning", "Tempo-Entries", "Tempo-Entries-Final", "Tempo-Exits", "Tempo-Exits-Final", "Tempo-Evening"
foreach ($n in $names) { if (Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $n -Confirm:$false } }
if ($Remove) { Write-Host "Removed all Tempo tasks."; return }

$python = & python -c "import sys; print(sys.executable)"
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }
$weekdays = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited

function Add-Job($name, $job, $times, $extra = "") {
    $action = New-ScheduledTaskAction -Execute $pythonw -Argument "-m tempo.sched $job $extra".Trim() -WorkingDirectory $repo
    $triggers = foreach ($t in $times) { New-ScheduledTaskTrigger -Weekly -DaysOfWeek $weekdays -At $t }
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $triggers -Settings $settings -Principal $principal `
        -Description "Tempo $job ($extra). Idempotent; see tempo/sched.py" | Out-Null
    Write-Host ("{0,-22} {1}" -f $name, ($times -join ", "))
}

Add-Job "Tempo-Morning"       "morning" @("06:30")
Add-Job "Tempo-Entries"       "entries" @("09:40", "09:55", "10:20", "11:00", "12:00", "13:30")
Add-Job "Tempo-Entries-Final" "entries" @("15:00") "--final"
Add-Job "Tempo-Exits"         "exits"   @("15:46", "15:50")
Add-Job "Tempo-Exits-Final"   "exits"   @("15:55") "--final"
Add-Job "Tempo-Evening"       "evening" @("16:20", "18:00")
