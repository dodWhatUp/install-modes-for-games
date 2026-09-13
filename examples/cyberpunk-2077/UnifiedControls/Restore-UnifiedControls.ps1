param(
    [Parameter(Mandatory)][string]$GameDirectory,
    [switch]$Apply
)
$ErrorActionPreference='Stop'
$game=(Resolve-Path -LiteralPath $GameDirectory).Path.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $game 'Cyberpunk2077.exe'))) { throw 'GameDirectory must be the real Cyberpunk bin/x64 directory' }
$snapshot=$PSScriptRoot
$manifest=Get-Content "$snapshot\manifest.json" -Raw|ConvertFrom-Json
foreach($entry in $manifest){
    $backup=Join-Path "$snapshot\game" $entry.relative
    $target=[IO.Path]::GetFullPath((Join-Path $game $entry.relative))
    if(!$target.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe manifest path'}
    if((Get-FileHash $backup).Hash -ne $entry.currentHash){throw "Backup hash mismatch: $($entry.relative)"}
}
if(!$Apply){Write-Output "Validated $($manifest.Count) original files. Use -Apply with Cyberpunk and Steam closed.";return}
$busy=@(Get-Process -ErrorAction SilentlyContinue|Where-Object ProcessName -Match '^(Cyberpunk2077|REDlauncher|REDprelauncher|steam|steamwebhelper|ShaderCompileWorker|dxc|fxc)$')
if($busy.Count){throw 'Close Cyberpunk, launchers, Steam and shader compilers first'}
$preserved=Join-Path $snapshot ('before-rollback-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $preserved|Out-Null
foreach($entry in $manifest){
    $current=Join-Path $game $entry.relative
    $to=Join-Path $preserved $entry.relative
    New-Item -ItemType Directory -Path (Split-Path $to) -Force|Out-Null
    if(Test-Path $current){Copy-Item -LiteralPath $current -Destination $to}
}
foreach($entry in $manifest){Copy-Item -LiteralPath (Join-Path "$snapshot\game" $entry.relative) -Destination (Join-Path $game $entry.relative)}
if(Test-Path "$snapshot\external\driver-before.json"){
    & "$snapshot\driver-profile.exe" restore "$snapshot\external\driver-before.json"
    if($LASTEXITCODE){throw 'Files restored, but driver settings restore failed'}
}
foreach($entry in $manifest){if((Get-FileHash (Join-Path $game $entry.relative)).Hash -ne $entry.currentHash){throw 'Restored file hash mismatch'}}
Write-Output 'Restored previous controls, NVIDIA runtimes and per-game driver settings. NR slot JSON and game saves were preserved.'
