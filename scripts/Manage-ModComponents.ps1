#Requires -Version 5.1
<#
.SYNOPSIS
Imports and switches independent, explicitly mapped mod components with private CAS snapshots.
.DESCRIPTION
Run Get-Help -Detailed, or read docs/MOD-COMPONENTS.md. Never extracts archives or executes
package scripts. All target roots must already exist. Import does not change game files.
Overlapping active owners, changed installed files, reparse points, unsafe names, running
games/launchers and unmet dependencies fail closed. No recursive target deletion is used.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Import','Enable','Disable','Status','Plan','Recover','CaptureCurrent','Snapshot')][string]$Command,
    [Parameter(Mandatory)][string]$StateRoot,
    [Parameter(Mandatory)][string]$RootsFile,
    [string]$PackagePath,
    [string]$ComponentId,
    [string]$SnapshotFiles,
    [ValidateSet('Enable','Disable')][string]$Operation = 'Enable'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:DefaultStopped = @('Cyberpunk2077','REDlauncher','REDprelauncher','steam','steamwebhelper',
    'EpicGamesLauncher','EpicWebHelper','GalaxyClient','GalaxyClientService','GalaxyCommunication',
    'Vortex','ModOrganizer','RHI','ShaderCompileWorker','dxc','fxc','REDmod','redscript','scc','CrashReporter')

function Get-Optional($Object, [string]$Name, $Default) {
    if ($Object -is [Collections.IDictionary]) {
        if ($Object.Contains($Name)) { return $Object[$Name] }
    } elseif ($null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]) { return $Object.$Name }
    return $Default
}
function Assert-Id([string]$Id) {
    if ($Id -cnotmatch '^[a-z0-9][a-z0-9._-]{0,79}$') { throw "Invalid component/root identifier: $Id" }
}
function Get-Full([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw "Absolute path required: $Path" }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd([char[]]'\/')
    if ($full -match '^\\\\' -or $full.Length -le 3) { throw 'UNC paths and drive roots are not allowed.' }
    return $full
}
function Test-Inside([string]$Path, [string]$Root) {
    return $Path.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}
function Assert-NoLinks([string]$Path) {
    $cursor = $Path
    while ($cursor) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point forbidden: $cursor" }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Get-SafePath([string]$Root, [string]$Relative) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or [IO.Path]::IsPathRooted($Relative) -or $Relative -match '[:*?"<>|\x00-\x1F]') {
        throw "Unsafe relative path: $Relative"
    }
    foreach ($segment in ($Relative -split '[\\/]')) {
        if ($segment -in @('', '.', '..') -or $segment -match '[. ]$' -or
            $segment -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)') { throw "Unsafe path segment: $Relative" }
    }
    $full = [IO.Path]::GetFullPath((Join-Path $Root ($Relative.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    if (-not (Test-Inside $full $Root) -or $full -eq $Root) { throw "Path escapes root: $Relative" }
    Assert-NoLinks $full
    return $full
}
function Get-Target($File) {
    if (-not $script:Roots.Contains([string]$File.root)) { throw "Unknown root: $($File.root)" }
    return Get-SafePath $script:Roots[[string]$File.root] ([string]$File.path)
}
function Get-Key($File) { return (Get-Target $File).ToLowerInvariant() }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Read-Json([string]$Path) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Write-Json([string]$Path, $Object) {
    Assert-NoLinks $Path
    $temp = $Path + '.tmp-' + [guid]::NewGuid().ToString('N')
    try {
        [IO.File]::WriteAllText($temp, ($Object | ConvertTo-Json -Depth 60), [Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temp, $Path, [NullString]::Value) }
        else { [IO.File]::Move($temp, $Path) }
    } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
}
function Get-Blob([string]$Hash) {
    if ($Hash -cnotmatch '^[a-f0-9]{64}$') { throw 'Invalid content hash in state.' }
    return Get-SafePath $script:StateDirectory ('blobs/' + $Hash)
}
function Assert-Blob([string]$Hash) {
    $path = Get-Blob $Hash
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Hash $path) -ne $Hash) { throw "Missing/corrupt snapshot blob: $Hash" }
    return $path
}
function Save-Blob([string]$Path) {
    Assert-NoLinks $Path
    $hash = Get-Hash $Path
    $dest = Get-Blob $hash
    if (-not (Test-Path -LiteralPath $dest)) { [IO.File]::Copy($Path, $dest, $false) }
    $null = Assert-Blob $hash
    return $hash
}
function Get-Record($File, [switch]$Preserve) {
    $path = Get-Target $File
    if (Test-Path -LiteralPath $path -PathType Container) { throw "Target is a directory: $path" }
    $record = [ordered]@{ root = [string]$File.root; path = [string]$File.path; exists = $false; sha256 = $null;
        length = 0; lastWriteTimeUtc = $null; fileVersion = $null; productVersion = $null; attributes = $null }
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $item = Get-Item -LiteralPath $path -Force
        $record.exists = $true
        $record.sha256 = if ($Preserve) { Save-Blob $path } else { Get-Hash $path }
        $record.length = $item.Length
        $record.lastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
        $record.fileVersion = $item.VersionInfo.FileVersion
        $record.productVersion = $item.VersionInfo.ProductVersion
        $record.attributes = [int]$item.Attributes
    }
    return [pscustomobject]$record
}
function Test-Same($Left, $Right) {
    return ($Left.exists -eq $Right.exists -and ((-not $Left.exists) -or $Left.sha256 -eq $Right.sha256))
}
function Set-Record($Record) {
    $path = Get-Target $Record
    Assert-NoLinks $path
    if ($Record.exists) {
        $source = Assert-Blob $Record.sha256
        $parent = [IO.Path]::GetDirectoryName($path)
        $null = [IO.Directory]::CreateDirectory($parent)
        Assert-NoLinks $parent
        $temp = Join-Path $parent ('.mod-component-' + [guid]::NewGuid().ToString('N') + '.tmp')
        try {
            [IO.File]::Copy($source, $temp, $false)
            Assert-NoLinks $path
            if (Test-Path -LiteralPath $path -PathType Leaf) { [IO.File]::Replace($temp, $path, [NullString]::Value) }
            else { [IO.File]::Move($temp, $path) }
            if ($Record.lastWriteTimeUtc) { [IO.File]::SetLastWriteTimeUtc($path, [datetime]::Parse($Record.lastWriteTimeUtc).ToUniversalTime()) }
        } finally { if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force } }
    } elseif (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -ErrorAction Stop }
}
function Assert-Stopped($Extra = @()) {
    $names = @($script:DefaultStopped + @($Extra) | Sort-Object -Unique)
    $running = @(Get-Process -ErrorAction Stop | Where-Object { $names -icontains $_.ProcessName })
    if ($running.Count) { throw ('Close required processes first: ' + (($running | Select-Object -ExpandProperty ProcessName -Unique) -join ', ')) }
    # Also catch processes launched from a supplied root, including renamed executables.
    foreach ($process in @(Get-Process -ErrorAction Stop)) {
        $imagePath = $null
        try { $imagePath = $process.Path } catch { continue }
        if ($imagePath) {
            foreach ($root in $script:Roots.Values) {
                if (Test-Inside $imagePath $root) { throw "Process loaded from managed root: $($process.ProcessName)" }
            }
        }
    }
}
function Get-Component([string]$Id) {
    Assert-Id $Id
    $found = @($script:State.components | Where-Object { $_.id -ceq $Id })
    if ($found.Count -ne 1) { throw "Component is not imported: $Id" }
    return $found[0]
}
function Get-Plan($Component, [string]$Action) {
    $active = @($script:State.components | Where-Object { $_.enabled })
    if ($Action -eq 'Enable') {
        if ($Component.enabled) { throw "Already enabled: $($Component.id)" }
        foreach ($dep in @($Component.dependencies)) {
            if (-not (Get-Component $dep).enabled) { throw "Enable dependency first: $dep" }
        }
        $owners = @{}
        foreach ($other in $active) { foreach ($file in $other.files) { $owners[(Get-Key $file)] = $other.id } }
        foreach ($file in $Component.files) {
            $key = Get-Key $file
            if ($owners.ContainsKey($key)) { throw "Overlapping owner $($owners[$key]) for $($file.path); reviewed deltas require a separate combined component." }
            $null = Assert-Blob $file.sha256
        }
        return @($Component.files | ForEach-Object { [pscustomobject]@{
            root = $_.root; path = $_.path; exists = $true; sha256 = $_.sha256; length = $_.length;
            lastWriteTimeUtc = $_.lastWriteTimeUtc; fileVersion = $_.fileVersion; productVersion = $_.productVersion; attributes = $_.attributes
        } })
    }
    if (-not $Component.enabled) { throw "Already disabled: $($Component.id)" }
    foreach ($other in $active) {
        if (@($other.dependencies) -contains $Component.id) { throw "Disable dependent first: $($other.id)" }
    }
    foreach ($file in $Component.files) {
        $current = Get-Record $file
        if (-not $current.exists -or $current.sha256 -ne $file.sha256) { throw "External drift preserved; refusing to overwrite/remove: $($file.root)/$($file.path)" }
    }
    foreach ($file in @($Component.before)) { if ($file.exists) { $null = Assert-Blob $file.sha256 } }
    return @($Component.before)
}
function Save-Snapshot([string]$Phase, [string]$Action, $Component, $Records, [string]$Transaction) {
    $path = Get-SafePath $script:StateDirectory ('snapshots/' + $Transaction + '-' + $Phase + '.json')
    Write-Json $path ([ordered]@{ schemaVersion = 1; timestampUtc = [datetime]::UtcNow.ToString('o');
        transaction = $Transaction; phase = $Phase; action = $Action; component = $Component.id;
        version = $Component.version; source = $Component.source; roots = $script:Roots; files = @($Records);
        context = @($Component.capture | ForEach-Object { Get-Record $_ -Preserve }) })
    return $path
}

$script:StateDirectory = Get-Full $StateRoot
Assert-NoLinks $script:StateDirectory
$repoCandidate = Get-Full (Split-Path -Parent $PSScriptRoot)
# A private standalone copy has no repository adjacent to it. In the source checkout,
# the repository guard continues to protect all history and tracked files.
$repoRoot = if (Test-Path -LiteralPath (Join-Path $repoCandidate 'preferences/GENERAL.md') -PathType Leaf) { $repoCandidate } else { $null }
if ($repoRoot -and (Test-Inside $script:StateDirectory $repoRoot)) { throw 'Private state must be outside the repository.' }
if (Test-Inside ([IO.Path]::GetFullPath($PSCommandPath)) $script:StateDirectory) { throw 'State directory must not contain the controller script.' }
$rootsSource = Get-Full $RootsFile
Assert-NoLinks $rootsSource
$rootInput = Read-Json $rootsSource
$script:Roots = [ordered]@{}
foreach ($property in $rootInput.PSObject.Properties) {
    Assert-Id $property.Name
    $root = Get-Full ([string]$property.Value)
    Assert-NoLinks $root
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Managed root does not exist: $root" }
    if ((Test-Inside $root $script:StateDirectory) -or (Test-Inside $script:StateDirectory $root)) { throw 'State and target roots must not overlap.' }
    if ($repoRoot -and ((Test-Inside $root $repoRoot) -or (Test-Inside $repoRoot $root))) { throw 'Managed roots must not overlap the repository.' }
    foreach ($prior in $script:Roots.Values) { if ((Test-Inside $root $prior) -or (Test-Inside $prior $root)) { throw 'Managed roots must not overlap each other.' } }
    $script:Roots[$property.Name] = $root
}
if (-not $script:Roots.Count) { throw 'At least one managed root is required.' }
if (-not (Test-Path -LiteralPath $script:StateDirectory)) {
    if ($Command -ne 'Import') { throw 'Import a component to initialize private state first.' }
    $null = [IO.Directory]::CreateDirectory($script:StateDirectory)
}
Assert-NoLinks $script:StateDirectory
$statePath = Get-SafePath $script:StateDirectory 'state.json'
$pendingPath = Get-SafePath $script:StateDirectory 'pending.json'
$lockPath = Get-SafePath $script:StateDirectory 'manager.lock'
$lock = $null
try {
    $lock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    foreach ($folder in @('blobs','snapshots')) {
        $sub = Get-SafePath $script:StateDirectory $folder
        $null = [IO.Directory]::CreateDirectory($sub)
    }
    $script:State = if (Test-Path -LiteralPath $statePath) { Read-Json $statePath }
        else { [pscustomobject]@{ schemaVersion = 1; roots = [pscustomobject]$script:Roots; components = @(); baseline = @() } }
    if ($script:State.schemaVersion -ne 1) { throw 'Unsupported state schema.' }
    $savedRoots = @($script:State.roots.PSObject.Properties)
    if ($savedRoots.Count -ne $script:Roots.Count) { throw 'Root mapping differs from initialized state.' }
    foreach ($entry in $savedRoots) {
        if (-not $script:Roots.Contains($entry.Name) -or $script:Roots[$entry.Name] -ine $entry.Value) { throw 'Root mapping differs from initialized state.' }
    }
    if ((Test-Path -LiteralPath $pendingPath) -and $Command -notin @('Recover','Status','Snapshot')) { throw 'Interrupted transaction detected. Inspect Status, then use Recover.' }

    switch ($Command) {
        'Status' {
            [pscustomobject]@{ stateRoot = $script:StateDirectory; pendingRecovery = (Test-Path -LiteralPath $pendingPath);
                components = @($script:State.components | ForEach-Object {
                    $component = $_
                    [pscustomobject]@{ id = $component.id; version = $component.version; enabled = $component.enabled;
                        dependencies = @($component.dependencies); files = @($component.files).Count;
                        localRevision = (Get-Optional $component 'localRevision' 0);
                        drift = @($(if ($component.enabled) { foreach ($file in $component.files) {
                            $current = Get-Record $file
                            if (-not $current.exists -or $current.sha256 -ne $file.sha256) { "$($file.root)/$($file.path)" }
                        } })) }
                }) } | ConvertTo-Json -Depth 12
            break
        }
        'Import' {
            $package = Get-Full $PackagePath
            Assert-NoLinks $package
            if ((Test-Inside $package $script:StateDirectory) -or (Test-Inside $script:StateDirectory $package)) { throw 'Package and state must be separate directories.' }
            $manifest = Read-Json (Get-SafePath $package 'component.json')
            Assert-Id ([string]$manifest.id)
            if ($manifest.schemaVersion -ne 1 -or [string]::IsNullOrWhiteSpace($manifest.version) -or [string]::IsNullOrWhiteSpace($manifest.source)) { throw 'Manifest requires schemaVersion 1, version and source.' }
            if (@($script:State.components | Where-Object { $_.id -ceq $manifest.id }).Count) { throw 'Component ID already imported; use a new versioned ID instead of rewriting recovery history.' }
            $deps = @(Get-Optional $manifest 'dependencies' @())
            foreach ($dep in $deps) { Assert-Id ([string]$dep); if ($dep -eq $manifest.id) { throw 'Self dependency forbidden.' } }
            $seen = @{}
            $files = @(foreach ($file in @($manifest.files)) {
                $key = Get-Key $file
                if ($seen.ContainsKey($key)) { throw "Duplicate destination: $($file.path)" }
                $seen[$key] = $true
                $source = Get-SafePath $package ([string]$file.payload)
                if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing payload: $($file.payload)" }
                $item = Get-Item -LiteralPath $source -Force
                [pscustomobject]@{ root = [string]$file.root; path = ([string]$file.path).Replace('\','/'); sha256 = (Save-Blob $source);
                    length = $item.Length; lastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o'); fileVersion = $item.VersionInfo.FileVersion;
                    productVersion = $item.VersionInfo.ProductVersion; attributes = [int]$item.Attributes }
            })
            if (-not $files.Count) { throw 'Empty components are not supported.' }
            # A destination file cannot also be the parent directory of another file.
            $keys = @($seen.Keys)
            foreach ($left in $keys) { foreach ($right in $keys) { if ($left -ne $right -and (Test-Inside $left $right)) { throw 'Destination file/directory collision.' } } }
            $capture = @(Get-Optional $manifest 'capture' @())
            foreach ($entry in $capture) { $null = Get-Target $entry }
            $stopped = @(Get-Optional $manifest 'requiredStoppedProcesses' @())
            foreach ($name in $stopped) { if ([string]$name -notmatch '^[A-Za-z0-9_. -]+$') { throw 'Invalid process name.' } }
            $component = [pscustomobject]@{ id = [string]$manifest.id; version = [string]$manifest.version; source = [string]$manifest.source;
                dependencies = $deps; requiredStoppedProcesses = $stopped; capture = $capture; files = $files;
                enabled = $false; before = @(); importedUtc = [datetime]::UtcNow.ToString('o') }
            $script:State.components = @($script:State.components) + @($component)
            Write-Json $statePath $script:State
            [pscustomobject]@{ action = 'Imported'; id = $component.id; files = $files.Count; targetFilesChanged = 0 }
            break
        }
        'Snapshot' {
            $components = if ($ComponentId) { @(Get-Component $ComponentId) } else { @($script:State.components) }
            $stopped = @($script:State.components | Where-Object { $_.enabled } | ForEach-Object { $_.requiredStoppedProcesses })
            Assert-Stopped $stopped
            $entries = @($components | ForEach-Object { $_.files; $_.capture })
            if ($SnapshotFiles) {
                $extraPath = Get-Full $SnapshotFiles
                Assert-NoLinks $extraPath
                $extraEntries = Read-Json $extraPath
                $entries += @($extraEntries)
            }
            $seen = @{}
            $records = @(foreach ($entry in $entries) {
                $key = Get-Key $entry
                if (-not $seen.ContainsKey($key)) { $seen[$key] = $true; Get-Record $entry -Preserve }
            })
            $transaction = [datetime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [guid]::NewGuid().ToString('N')
            $snapshotPath = Get-SafePath $script:StateDirectory ('snapshots/' + $transaction + '-manual.json')
            Write-Json $snapshotPath ([ordered]@{ schemaVersion = 1; timestampUtc = [datetime]::UtcNow.ToString('o');
                action = 'Snapshot'; roots = $script:Roots; components = @($components | ForEach-Object { $_.id });
                files = $records; targetFilesChanged = 0 })
            [pscustomobject]@{ action = 'Snapshot'; files = $records.Count; snapshot = $snapshotPath; targetFilesChanged = 0 }
            break
        }
        'CaptureCurrent' {
            $component = Get-Component $ComponentId
            if (-not $component.enabled) { throw 'CaptureCurrent requires an enabled component.' }
            $stopped = @($component.requiredStoppedProcesses) + @($script:State.components | Where-Object { $_.enabled } | ForEach-Object { $_.requiredStoppedProcesses })
            Assert-Stopped $stopped
            $transaction = [datetime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [guid]::NewGuid().ToString('N')
            $current = @($component.files | ForEach-Object { Get-Record $_ -Preserve })
            $snapshot = Save-Snapshot 'current' 'CaptureCurrent' $component $current $transaction
            if (@($current | Where-Object { -not $_.exists }).Count) { throw 'CaptureCurrent refuses missing owned files; current state was preserved.' }
            # Keep the original installed payload and pre-enable rollback separate from intentional local edits.
            $previous = Get-SafePath $script:StateDirectory ('snapshots/' + $transaction + '-previous-payload.json')
            foreach ($file in $component.files) { $null = Assert-Blob $file.sha256 }
            Write-Json $previous ([ordered]@{ schemaVersion = 1; action = 'CaptureCurrent'; component = $component.id;
                version = $component.version; source = $component.source; files = @($component.files);
                rollbackBefore = @($component.before); localRevision = (Get-Optional $component 'localRevision' 0) })
            $changed = @()
            for ($i = 0; $i -lt $current.Count; $i++) {
                if (-not (Test-Same (Get-Record $current[$i]) $current[$i])) { throw "Concurrent target modification: $($current[$i].path)" }
                if ($component.files[$i].sha256 -ne $current[$i].sha256) { $changed += "$($current[$i].root)/$($current[$i].path)" }
            }
            if ($changed.Count) {
                $revision = [int](Get-Optional $component 'localRevision' 0) + 1
                $component.files = $current
                $component | Add-Member -MemberType NoteProperty -Name localRevision -Value $revision -Force
                $component | Add-Member -MemberType NoteProperty -Name capturedUtc -Value ([datetime]::UtcNow.ToString('o')) -Force
                Write-Json $statePath $script:State
            }
            [pscustomobject]@{ action = 'CaptureCurrent'; id = $component.id; changed = $changed; currentSnapshot = $snapshot;
                previousPayloadSnapshot = $previous; targetFilesChanged = 0; localRevision = (Get-Optional $component 'localRevision' 0) }
            break
        }
        'Recover' {
            if (-not (Test-Path -LiteralPath $pendingPath)) { throw 'No interrupted transaction to recover.' }
            $journal = Read-Json $pendingPath
            Assert-Stopped @($journal.requiredStoppedProcesses)
            # Preserve anything changed since interruption, even when recovery must refuse it.
            $current = @($journal.before | ForEach-Object { Get-Record $_ -Preserve })
            Write-Json (Get-SafePath $script:StateDirectory ('snapshots/' + $journal.transaction + '-recovery-current-' + [guid]::NewGuid().ToString('N') + '.json')) $current
            for ($i = 0; $i -lt $current.Count; $i++) {
                if (-not (Test-Same $current[$i] $journal.before[$i]) -and -not (Test-Same $current[$i] $journal.after[$i])) {
                    throw "Recovery refused external drift: $($current[$i].path)"
                }
                if ($journal.before[$i].exists) { $null = Assert-Blob $journal.before[$i].sha256 }
            }
            for ($i = $current.Count - 1; $i -ge 0; $i--) {
                if (-not (Test-Same $current[$i] $journal.before[$i])) { Set-Record $journal.before[$i] }
            }
            Write-Json $statePath $journal.stateBefore
            Write-Json (Get-SafePath $script:StateDirectory ('snapshots/' + $journal.transaction + '-recovered.json')) @($journal.before | ForEach-Object { Get-Record $_ -Preserve })
            Remove-Item -LiteralPath $pendingPath
            [pscustomobject]@{ action = 'Recovered'; transaction = $journal.transaction }
            break
        }
        default {
            $component = Get-Component $ComponentId
            $action = if ($Command -eq 'Plan') { $Operation } else { $Command }
            $allStopped = @($component.requiredStoppedProcesses) + @($script:State.components | Where-Object { $_.enabled } | ForEach-Object { $_.requiredStoppedProcesses })
            Assert-Stopped $allStopped
            $transaction = [datetime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [guid]::NewGuid().ToString('N')
            # Snapshot BEFORE drift/dependency validation for mutations: refusal still preserves current edited settings.
            if ($Command -ne 'Plan') {
                $before = @($component.files | ForEach-Object { Get-Record $_ -Preserve })
                $snapshot = Save-Snapshot 'before' $action $component $before $transaction
            }
            $after = @(Get-Plan $component $action)
            if ($Command -eq 'Plan') {
                [pscustomobject]@{ action = $action; id = $component.id; files = @($after | ForEach-Object {
                    $current = Get-Record $_
                    [pscustomobject]@{ root = $_.root; path = $_.path; before = $current.sha256; after = $_.sha256;
                        change = $(if (Test-Same $current $_) { 'Unchanged' } elseif (-not $_.exists) { 'Remove' } elseif ($current.exists) { 'Replace' } else { 'Add' }) }
                }) } | ConvertTo-Json -Depth 12
                break
            }
            $stateBefore = $script:State | ConvertTo-Json -Depth 60 | ConvertFrom-Json
            $journal = [ordered]@{ schemaVersion = 1; transaction = $transaction; action = $action; component = $component.id;
                requiredStoppedProcesses = $allStopped; before = $before; after = $after; stateBefore = $stateBefore }
            Write-Json $pendingPath $journal
            $applied = [Collections.Generic.List[int]]::new()
            try {
                Assert-Stopped $allStopped
                for ($i = 0; $i -lt $after.Count; $i++) {
                    $current = Get-Record $before[$i]
                    if (-not (Test-Same $current $before[$i])) { throw "Concurrent target modification: $($current.path)" }
                    # Track before writing so a post-replacement timestamp/verification failure also rolls back.
                    $applied.Add($i)
                    Set-Record $after[$i]
                    if (-not (Test-Same (Get-Record $after[$i]) $after[$i])) { throw "Write verification failed: $($after[$i].path)" }
                }
                if ($action -eq 'Enable') {
                    $component.before = $before
                    $baselineKeys = @{}
                    foreach ($entry in @($script:State.baseline)) { $baselineKeys[(Get-Key $entry)] = $true }
                    foreach ($entry in $before) { if (-not $baselineKeys.ContainsKey((Get-Key $entry))) { $script:State.baseline = @($script:State.baseline) + @($entry) } }
                    $component.enabled = $true
                } else { $component.enabled = $false }
                $verified = @($component.files | ForEach-Object { Get-Record $_ -Preserve })
                $afterSnapshot = Save-Snapshot 'after' $action $component $verified $transaction
                Write-Json $statePath $script:State
                Remove-Item -LiteralPath $pendingPath
                [pscustomobject]@{ action = $action; id = $component.id; files = $after.Count; beforeSnapshot = $snapshot; afterSnapshot = $afterSnapshot }
            } catch {
                $originalError = $_
                try {
                    Assert-Stopped $allStopped
                    for ($j = $applied.Count - 1; $j -ge 0; $j--) {
                        $index = $applied[$j]
                        $now = Get-Record $before[$index] -Preserve
                        if (Test-Same $now $before[$index]) { continue }
                        if (-not (Test-Same $now $after[$index])) { throw "External drift during rollback: $($now.path)" }
                        Set-Record $before[$index]
                    }
                    Write-Json $statePath $stateBefore
                    $null = Save-Snapshot 'rolled-back' $action $component @($component.files | ForEach-Object { Get-Record $_ -Preserve }) $transaction
                    Remove-Item -LiteralPath $pendingPath
                } catch { throw "Mutation failed: $($originalError.Exception.Message). Recovery incomplete; pending journal retained: $($_.Exception.Message)" }
                throw "Mutation failed and was rolled back: $($originalError.Exception.Message)"
            }
        }
    }
} finally { if ($null -ne $lock) { $lock.Dispose() } }
