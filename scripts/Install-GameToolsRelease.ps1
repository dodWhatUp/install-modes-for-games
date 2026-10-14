[CmdletBinding()]
param(
    [ValidateSet('Inspect','Stage','UpgradeStudio')][string]$Mode = 'Inspect',
    [string]$Destination,
    [string]$ExpectedInstalledManifest
)
$ErrorActionPreference = 'Stop'
# Fixed source files only. Never starts AHK/Hub/game or edits settings/profiles.
$taskRelease = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskManifest = Join-Path $taskRelease 'MANIFEST.json'
if (!(Test-Path -LiteralPath $taskManifest -PathType Leaf)) { throw 'Run from the verified extracted release, not an unmanifested source checkout.' }
$taskData = Get-Content -Raw -LiteralPath $taskManifest | ConvertFrom-Json
function Assert-LocalPath([string]$Path) {
    $taskResolved = [IO.Path]::GetFullPath($Path)
    if ($taskResolved.StartsWith('\\') -or $taskResolved -eq [IO.Path]::GetPathRoot($taskResolved)) { throw 'Use an explicit local non-root directory.' }
    $taskCheck = $taskResolved
    while ($taskCheck) {
        if (Test-Path -LiteralPath $taskCheck) {
            $taskItem = Get-Item -LiteralPath $taskCheck -Force
            if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked/reparse target refused.' }
        }
        $taskParent = Split-Path -Parent $taskCheck
        if ($taskParent -eq $taskCheck) { break }
        $taskCheck = $taskParent
    }
    return $taskResolved
}
$taskRows = @()
foreach ($taskEntry in $taskData.files) {
    if ($taskEntry.path -notmatch '^[A-Za-z0-9_./+-]+$' -or $taskEntry.path.Split('/') -contains '..') { throw 'Unsafe release member.' }
    $taskFile = Join-Path $taskRelease $taskEntry.path
    $null = Assert-LocalPath $taskFile
    if (!(Test-Path -LiteralPath $taskFile -PathType Leaf) -or (Get-Item -LiteralPath $taskFile).Length -ne $taskEntry.bytes -or
        (Get-FileHash -LiteralPath $taskFile).Hash -ne $taskEntry.sha256) { throw "Release bytes differ: $($taskEntry.path)" }
    $taskRows += $taskEntry
}
if ($taskData.component_versions.tool_hub -ne '0.11.0') { throw 'This installer accepts only the tested Hub 0.11.0 release.' }
if ($Mode -eq 'Inspect') {
    [pscustomobject]@{version='0.11.0';files_verified=$taskRows.Count;runtime='Python 3.11+ with Tk and Pillow; AutoHotkey v2.0.30 for optional Studio';activation='none';settings_changes=$false} | ConvertTo-Json
    return
}
if (!$Destination) { throw 'Destination is required for an explicit install operation.' }
$taskTarget = Assert-LocalPath $Destination
if ($Mode -eq 'Stage') {
    if (Test-Path -LiteralPath $taskTarget) { throw 'Stage requires a NEW versioned directory; never merge over a working host.' }
    New-Item -ItemType Directory -Path $taskTarget | Out-Null
    foreach ($taskEntry in $taskRows) {
        $taskTo = Join-Path $taskTarget $taskEntry.path
        New-Item -ItemType Directory -Path (Split-Path -Parent $taskTo) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $taskRelease $taskEntry.path) -Destination $taskTo
        if ((Get-FileHash -LiteralPath $taskTo).Hash -ne $taskEntry.sha256) { throw 'Staged readback mismatch; preserve incomplete stage for inspection.' }
    }
    Copy-Item -LiteralPath $taskManifest -Destination (Join-Path $taskTarget 'MANIFEST.json')
    [pscustomobject]@{staged=$taskTarget;verified=$taskRows.Count;activation='none';restore='Original host/settings/profiles remain untouched.'} | ConvertTo-Json
    return
}
if (!$ExpectedInstalledManifest) { throw 'Upgrade requires a fresh explicit expected-file hash manifest.' }
if (@(Get-Process -Name 'AutoHotkey*' -ErrorAction SilentlyContinue).Count) { throw 'Close AHK hosts normally before upgrade; this tool never terminates them.' }
$taskExpected = Get-Content -Raw -LiteralPath $ExpectedInstalledManifest | ConvertFrom-Json
$taskNames = [ordered]@{
    'AzeronOverlayStudio.ahk'='examples/game-input/AzeronOverlayStudio.integrated.ahk'
    'GameInputModule.ahk'='examples/game-input/GameInputModule.ahk'
    'OverlayStudioGameInput.ahk'='examples/game-input/OverlayStudioGameInput.ahk'
    'StudioPictureModule.ahk'='examples/game-input/StudioPictureModule.ahk'
    'StudioOverlayGroups.ahk'='examples/game-input/StudioOverlayGroups.ahk'
}
foreach ($taskName in $taskNames.Keys) {
    $taskTo = Join-Path $taskTarget $taskName; $null = Assert-LocalPath $taskTo
    $taskHash = if (Test-Path -LiteralPath $taskTo -PathType Leaf) { (Get-FileHash -LiteralPath $taskTo).Hash } else { 'absent' }
    if ($taskExpected.$taskName -ne $taskHash) { throw "Installed source drift: $taskName. Reconcile newer features, do not overwrite." }
}
$taskBackup = Join-Path $taskTarget ('groups-before-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskBackup | Out-Null
Copy-Item -LiteralPath $ExpectedInstalledManifest -Destination (Join-Path $taskBackup 'EXPECTED.json')
foreach ($taskName in $taskNames.Keys) {
    $taskTo = Join-Path $taskTarget $taskName
    if (Test-Path -LiteralPath $taskTo) {
        Copy-Item -LiteralPath $taskTo -Destination (Join-Path $taskBackup $taskName)
        if ((Get-FileHash -LiteralPath (Join-Path $taskBackup $taskName)).Hash -ne $taskExpected.$taskName) { throw 'Backup hash mismatch.' }
    }
}
# Preserve the separate current installed settings before any source mutation.
$taskSettings = Join-Path $env:APPDATA 'AzeronOverlayStudio'
if (Test-Path -LiteralPath $taskSettings) {
    $null = Assert-LocalPath $taskSettings
    foreach ($taskSettingName in @('settings.ini','pictures-v3.ini')) {
        $taskSettingFile = Join-Path $taskSettings $taskSettingName
        if (Test-Path -LiteralPath $taskSettingFile -PathType Leaf) {
            $null = Assert-LocalPath $taskSettingFile
            Copy-Item -LiteralPath $taskSettingFile -Destination (Join-Path $taskBackup $taskSettingName)
            if ((Get-FileHash -LiteralPath $taskSettingFile).Hash -ne (Get-FileHash -LiteralPath (Join-Path $taskBackup $taskSettingName)).Hash) { throw 'Settings backup readback mismatch.' }
        }
    }
}
foreach ($taskName in $taskNames.Keys) {
    $taskTo = Join-Path $taskTarget $taskName
    $taskHash = if (Test-Path -LiteralPath $taskTo) { (Get-FileHash -LiteralPath $taskTo).Hash } else { 'absent' }
    if ($taskExpected.$taskName -ne $taskHash) { throw 'Concurrent source change; preserve the partial upgrade and rollback checkpoint.' }
    Copy-Item -LiteralPath (Join-Path $taskRelease $taskNames[$taskName]) -Destination $taskTo
    if ((Get-FileHash -LiteralPath $taskTo).Hash -ne (Get-FileHash -LiteralPath (Join-Path $taskRelease $taskNames[$taskName])).Hash) { throw 'Upgrade readback mismatch; restore only changed owned source files.' }
}
[pscustomobject]@{version='2.2.0-groups-preview.1';backup=$taskBackup;activation='none';settings_changes=$false;native_changes=$false;
    rollback='Close AHK normally. Preserve later source; copy original named AHK files from this checkpoint only. New modules may remain unused. Never restore all native profiles or settings.'} | ConvertTo-Json
