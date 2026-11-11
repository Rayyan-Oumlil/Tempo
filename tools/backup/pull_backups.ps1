# Copies the VPS's nightly backups to this PC (first choice for where backups live). Safe to run any time, any number of times:
# only files not already here are copied, and each is checked against its .sha256 before it is kept.
# Needs the ssh alias "tempo-vps" in ~/.ssh/config (the server address is never committed).
# Register: powershell -ExecutionPolicy Bypass -File tools\backup\pull_backups.ps1 -Register
param([switch]$Register, [string]$Dest = "$env:USERPROFILE\Backups\Tempo", [int]$Keep = 30)
$ErrorActionPreference = "Stop"
if ($Register) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $triggers = @(New-ScheduledTaskTrigger -Daily -At "22:00")
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName "Tempo backup pull" -Action $action -Trigger $triggers -Settings $settings -Force | Out-Null
    Write-Host "registered: daily 22:00; StartWhenAvailable runs it at the next wake if the PC was off"; exit 0
}
New-Item -ItemType Directory -Force $Dest | Out-Null
$remote = ssh tempo-vps "ls /opt/tempo/backups" | Where-Object { $_ -like "tempo-*.tar.gz" }
if (-not $remote) { throw "no backups listed on the VPS" }
foreach ($name in $remote) {
    if (Test-Path "$Dest\$name") { continue }
    scp -q "tempo-vps:/opt/tempo/backups/$name" "tempo-vps:/opt/tempo/backups/$name.sha256" $Dest
    if ($LASTEXITCODE -ne 0) { throw "scp failed for $name" }
    $want = (Get-Content "$Dest\$name.sha256").Split(" ")[0]
    $got = (Get-FileHash "$Dest\$name" -Algorithm SHA256).Hash.ToLower()
    if ($want -ne $got) { Remove-Item "$Dest\$name", "$Dest\$name.sha256"; throw "checksum mismatch for $name, deleted" }
    Write-Host "pulled $name"
}
Get-ChildItem $Dest -Filter "tempo-*.tar.gz" | Sort-Object Name -Descending | Select-Object -Skip $Keep | ForEach-Object {
    Remove-Item $_.FullName, "$($_.FullName).sha256" -ErrorAction SilentlyContinue }
Write-Host "backups on this PC: $((Get-ChildItem $Dest -Filter 'tempo-*.tar.gz').Count) in $Dest"
