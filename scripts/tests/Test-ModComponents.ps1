#Requires -Version 5.1
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$productionScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'Manage-ModComponents.ps1'
$base = Join-Path ([IO.Path]::GetTempPath()) ('mod-components-test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $base
$checks = 0
function Assert($Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
    $script:checks++
}
function Json([string]$Path, $Value) { [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 60), [Text.UTF8Encoding]::new($false)) }
function Read([string]$Path) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 }
function Expect-Failure([scriptblock]$Body, [string]$Pattern) {
    $message = ''
    try { & $Body | Out-Null } catch { $message = $_.Exception.Message }
    Assert ($message -match $Pattern) "Expected failure '$Pattern', got '$message'"
}
function Package([string]$Id, $Map, $Dependencies = @(), $Capture = @()) {
    $dir = Join-Path $base ('package-' + $Id)
    $null = New-Item -ItemType Directory -Path $dir
    $files = @()
    $n = 0
    foreach ($path in $Map.Keys) {
        $payload = 'file' + $n++ + '.txt'
        [IO.File]::WriteAllText((Join-Path $dir $payload), [string]$Map[$path])
        $files += [ordered]@{ root = 'game'; path = $path; payload = $payload }
    }
    Json (Join-Path $dir 'component.json') ([ordered]@{ schemaVersion = 1; id = $Id; version = '1.0'; source = 'https://example.invalid/test';
        dependencies = @($Dependencies); files = $files; capture = @($Capture) })
    return $dir
}
try {
    $game = Join-Path $base 'game'
    $user = Join-Path $base 'user'
    $stateDir = Join-Path $base 'state'
    $codeDir = Join-Path $base 'code/scripts'
    foreach ($dir in @($game,$user,$codeDir)) { $null = New-Item -ItemType Directory -Path $dir -Force }
    $roots = Join-Path $base 'roots.json'
    Json $roots ([ordered]@{ game = $game; user = $user })
    [IO.File]::WriteAllText((Join-Path $game 'stock.ini'), 'stock')
    [IO.File]::WriteAllText((Join-Path $game 'unrelated.txt'), 'untouched')
    [IO.File]::WriteAllText((Join-Path $user 'UserSettings.json'), '{"existing":true}')
    $source = Read $productionScript
    $tokens = $null; $parseErrors = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$parseErrors)
    Assert ($parseErrors.Count -eq 0) 'Production script parses cleanly'
    # Mock only the process inventory inside a private script copy. Production has no guard-bypass flag.
    # The original real guard is exercised separately below. Every managed path stays in this fixture.
    $guard = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-Stopped' }, $false)
    $fixtureSource = $source.Substring(0, $guard.Extent.StartOffset) + 'function Assert-Stopped($Extra = @()) {}' + $source.Substring($guard.Extent.EndOffset)
    $script:runner = Join-Path $codeDir 'Manage-ModComponents.ps1'
    [IO.File]::WriteAllText($script:runner, $fixtureSource)
    $script:common = @{ StateRoot = $stateDir; RootsFile = $roots }
    function Run([string]$Action, [string]$Id = '', [string]$PackagePath = '') {
        & $script:runner @script:common -Command $Action -ComponentId $Id -PackagePath $PackagePath
    }
    $a = Package 'a' ([ordered]@{ 'stock.ini' = 'a-stock'; 'mods/a.txt' = 'alpha' }) @() @(@{ root = 'user'; path = 'UserSettings.json' })
    $b = Package 'b' ([ordered]@{ 'mods/b.txt' = 'beta' })
    Run Import a $a | Out-Null; Run Import b $b | Out-Null
    Assert ((Read (Join-Path $game 'stock.ini')) -ceq 'stock') 'Import is game-read-only'
    $plan = Run Plan a | ConvertFrom-Json
    Assert ($plan.files.Count -eq 2 -and $plan.files[0].change -eq 'Replace') 'Plan identifies exact replacement and addition'
    Run Enable a | Out-Null; Run Enable b | Out-Null
    Assert ((Read (Join-Path $game 'stock.ini')) -ceq 'a-stock') 'Enable applies replacement'
    $snapshot = @(Get-ChildItem -LiteralPath (Join-Path $stateDir 'snapshots') -Filter '*-after.json' | Sort-Object Name)[0] | Get-Content -Raw | ConvertFrom-Json
    Assert ($snapshot.context.Count -eq 1 -and $snapshot.context[0].exists) 'Snapshot includes external configuration'
    Run Disable a | Out-Null
    Assert ((Read (Join-Path $game 'stock.ini')) -ceq 'stock') 'Disable restores pre-component stock bytes'
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'mods/a.txt'))) 'Disable removes only added owned file'
    Assert ((Read (Join-Path $game 'mods/b.txt')) -ceq 'beta') 'Out-of-order removal preserves later independent component'
    Assert ((Read (Join-Path $game 'unrelated.txt')) -ceq 'untouched') 'Unrelated file remains untouched'
    [IO.File]::WriteAllText((Join-Path $game 'mods/b.txt'), 'personal-edit')
    Expect-Failure { Run Disable b } 'External drift preserved'
    Assert ((Read (Join-Path $game 'mods/b.txt')) -ceq 'personal-edit') 'Drift survives refused disable'
    $hash = (Get-FileHash -LiteralPath (Join-Path $game 'mods/b.txt') -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert (Test-Path -LiteralPath (Join-Path $stateDir ('blobs/' + $hash))) 'Refused mutation still snapshots drift bytes'
    $status = Run Status | ConvertFrom-Json
    Assert (($status.components | Where-Object id -eq b).drift.Count -eq 1) 'Status reports drift'
    $captured = Run CaptureCurrent b
    Assert ($captured.targetFilesChanged -eq 0 -and $captured.localRevision -eq 1) 'CaptureCurrent records intentional local revision without target writes'
    Assert ((Read (Join-Path $game 'mods/b.txt')) -ceq 'personal-edit') 'CaptureCurrent leaves edited bytes unchanged'
    $previousPayload = Read $captured.previousPayloadSnapshot | ConvertFrom-Json
    Assert ($previousPayload.files[0].sha256 -ne $hash) 'CaptureCurrent keeps prior distributed payload hash'
    Assert (($previousPayload.rollbackBefore.Count -eq 1) -and -not $previousPayload.rollbackBefore[0].exists) 'CaptureCurrent preserves original pre-enable rollback'
    Assert (((Run Status | ConvertFrom-Json).components | Where-Object id -eq b).drift.Count -eq 0) 'CaptureCurrent reconciles drift explicitly'
    Run Disable b | Out-Null
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'mods/b.txt'))) 'Captured payload still restores original absent baseline on disable'
    Run Enable b | Out-Null
    Assert ((Read (Join-Path $game 'mods/b.txt')) -ceq 'personal-edit') 'Re-enable uses captured local choices'
    Remove-Item -LiteralPath (Join-Path $game 'mods/b.txt')
    Expect-Failure { Run CaptureCurrent b } 'refuses missing owned files'
    [IO.File]::WriteAllText((Join-Path $game 'mods/b.txt'), 'personal-edit')
    $extras = Join-Path $base 'snapshot-files.json'
    Json $extras @(@{ root = 'user'; path = 'UserSettings.json' })
    $manual = & $script:runner @script:common -Command Snapshot -ComponentId b -SnapshotFiles $extras
    $manualRecord = Read $manual.snapshot | ConvertFrom-Json
    Assert ($manualRecord.files.Count -eq 2 -and $manualRecord.targetFilesChanged -eq 0) 'Manual snapshot captures optional external config without changing targets'
    Assert ((Read (Join-Path $game 'mods/b.txt')) -ceq 'personal-edit') 'Snapshot preserves current owned payload'
    Run Disable b | Out-Null
    Expect-Failure { Run CaptureCurrent b } 'requires an enabled component'
    $c = Package 'c' ([ordered]@{ 'mods/c.txt' = 'charlie' }) @('a')
    Run Import c $c | Out-Null
    Expect-Failure { Run Enable c } 'Enable dependency first'
    Run Enable a | Out-Null; Run Enable c | Out-Null
    Expect-Failure { Run Disable a } 'Disable dependent first'
    $d = Package 'd' ([ordered]@{ 'mods/a.txt' = 'alpha' })
    Run Import d $d | Out-Null
    Expect-Failure { Run Enable d } 'Overlapping owner'
    Run Disable c | Out-Null; Run Disable a | Out-Null
    Expect-Failure { Run Import a $a } 'already imported'
    foreach ($badPath in @('../outside.txt','good/../outside.txt','C:/outside.txt','file.txt:stream','NUL.txt','tail.','empty//x')) {
        $unsafeId = 'unsafe-' + [guid]::NewGuid().ToString('N')
        $bad = Package $unsafeId ([ordered]@{ $badPath = 'bad' })
        Expect-Failure { Run Import $unsafeId $bad } 'Unsafe'
    }
    $outside = Join-Path $base 'outside'
    $null = New-Item -ItemType Directory -Path $outside
    $junction = Join-Path $game 'escape'
    $null = New-Item -ItemType Junction -Path $junction -Target $outside
    $linkPackage = Package 'link-target' ([ordered]@{ 'escape/file.txt' = 'bad' })
    Expect-Failure { Run Import link-target $linkPackage } 'Reparse point forbidden'
    Assert (-not (Test-Path -LiteralPath (Join-Path $outside 'file.txt'))) 'Junction escape wrote nothing'
    $null = [IO.Directory]::Delete($junction)
    $collision = Package 'collision' ([ordered]@{ 'thing' = 'a'; 'thing/child' = 'b' })
    Expect-Failure { Run Import collision $collision } 'file/directory collision'
    # A late write error must undo an earlier successful write without deleting unrelated data.
    [IO.File]::WriteAllText((Join-Path $game 'lock.txt'), 'lock-stock')
    $rollback = Package 'rollback' ([ordered]@{ 'first.txt' = 'first-added'; 'lock.txt' = 'lock-replaced' })
    Run Import rollback $rollback | Out-Null
    $locked = [IO.File]::Open((Join-Path $game 'lock.txt'), [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try { Expect-Failure { Run Enable rollback } 'was rolled back' } finally { $locked.Dispose() }
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'first.txt'))) 'Rollback removes first successfully written addition'
    Assert ((Read (Join-Path $game 'lock.txt')) -ceq 'lock-stock') 'Failed replacement preserves original'
    Assert (-not (Test-Path -LiteralPath (Join-Path $stateDir 'pending.json'))) 'Completed rollback clears journal'
    # Corrupt payload CAS fails before writing any target.
    $state = Read (Join-Path $stateDir 'state.json') | ConvertFrom-Json
    $blob = Join-Path $stateDir ('blobs/' + ($state.components | Where-Object id -eq rollback).files[0].sha256)
    $savedBlob = [IO.File]::ReadAllBytes($blob)
    [IO.File]::WriteAllText($blob, 'corrupt')
    Expect-Failure { Run Enable rollback } 'Missing/corrupt snapshot blob'
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'first.txt'))) 'Corrupt CAS fails without target write'
    [IO.File]::WriteAllBytes($blob, $savedBlob)
    # Simulate interruption after one replacement, using a previously captured activation journal.
    $stateBefore = Read (Join-Path $stateDir 'state.json') | ConvertFrom-Json
    Run Enable a | Out-Null
    $activeState = Read (Join-Path $stateDir 'state.json') | ConvertFrom-Json
    $component = $activeState.components | Where-Object id -eq a
    $desired = @($component.files | ForEach-Object { $_ | Add-Member -NotePropertyName exists -NotePropertyValue $true -PassThru })
    Json (Join-Path $stateDir 'pending.json') ([ordered]@{ transaction = 'test-interruption'; requiredStoppedProcesses = @();
        before = @($component.before); after = $desired; stateBefore = $stateBefore })
    Expect-Failure { Run Enable b } 'Interrupted transaction detected'
    Run Recover | Out-Null
    Assert ((Read (Join-Path $game 'stock.ini')) -ceq 'stock') 'Recovery restores replacement from journal'
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'mods/a.txt'))) 'Recovery removes journal-owned addition'
    Assert (-not ((Run Status | ConvertFrom-Json).components | Where-Object id -eq a).enabled) 'Recovery restores activation metadata'
    $realProcess = Get-Process -Id $PID
    $guardPackage = Package 'real-guard' ([ordered]@{ 'guard.txt' = 'must-not-write' })
    $guardManifest = Read (Join-Path $guardPackage 'component.json') | ConvertFrom-Json
    $guardManifest | Add-Member -NotePropertyName requiredStoppedProcesses -NotePropertyValue @($realProcess.ProcessName)
    Json (Join-Path $guardPackage 'component.json') $guardManifest
    & $productionScript @script:common -Command Import -PackagePath $guardPackage | Out-Null
    Expect-Failure { & $productionScript @script:common -Command Enable -ComponentId real-guard } 'Close required processes first'
    Assert (-not (Test-Path -LiteralPath (Join-Path $game 'guard.txt'))) 'Production process guard blocks before target mutation'
    [pscustomobject]@{ result = 'PASS'; checks = $checks; scope = 'Isolated temp fixtures; process inventory mocked except real production guard test'; fixture = $base }
} finally {
    # Deliberately retain this small fixture as test evidence. No recursive cleanup or live game access.
}
