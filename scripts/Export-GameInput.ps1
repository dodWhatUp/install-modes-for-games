param([Parameter(Mandatory = $true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskOut = [IO.Path]::GetFullPath($OutputDirectory)
if ($taskOut.Equals($taskRepo, [StringComparison]::OrdinalIgnoreCase) -or
    $taskOut.StartsWith($taskRepo + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose a new output directory outside the repository.'
}
if (Test-Path -LiteralPath $taskOut) {
    throw 'Output already exists. Choose a new directory; do not overwrite an earlier archive.'
}
$taskFiles = @(
    'docs/AGENT-GAME-INPUT.md',
    'examples/game-input/README.md',
    'examples/game-input/GameInputModule.ahk',
    'examples/game-input/Start-GameInput.ahk',
    'examples/game-input/HostIntegration.example.ahk',
    'examples/game-input/OTHER-CHAT-HANDOFF.txt',
    'examples/game-input/VALIDATION.json',
    'examples/game-input/baseline/ControlHelper-v031.ahk',
    'examples/skyrim-special-edition/Skyrim-F12-Test.ahk',
    'examples/skyrim-special-edition/README.md',
    'scripts/Export-GameInput.ps1'
)
$taskRows = @()
foreach ($taskRel in $taskFiles) {
    $taskSource = Join-Path $taskRepo $taskRel
    if (!(Test-Path -LiteralPath $taskSource -PathType Leaf)) { throw "Missing package source: $taskRel" }
    $taskText = [IO.File]::ReadAllText($taskSource)
    if ($taskText -match '[A-Za-z]:[\\/]+Users[\\/]+[^<>\\/\s]+[\\/]|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{25,}') {
        throw "Review private-path/credential candidate: $taskRel"
    }
    $taskHash = (Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
    if ($taskRel.EndsWith('ControlHelper-v031.ahk') -and
        $taskHash -ne 'EAFD9509DC8B7C579915668648AD20F000D377B5018B5ECE9D4CD9B43F7A46D8') {
        throw 'Historical baseline bytes differ; do not label this package byte-identical.'
    }
    $taskRows += [ordered]@{ path = $taskRel; bytes = (Get-Item -LiteralPath $taskSource).Length; sha256 = $taskHash }
}
New-Item -ItemType Directory -Path $taskOut | Out-Null
$taskStage = Join-Path $taskOut 'source'
New-Item -ItemType Directory -Path $taskStage | Out-Null
foreach ($taskRel in $taskFiles) {
    $taskDest = Join-Path $taskStage $taskRel
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskDest) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $taskRepo $taskRel) -Destination $taskDest
}
$taskManifest = [ordered]@{
    version = '0.5-preview.1'; created_utc = [DateTime]::UtcNow.ToString('o')
    source = 'https://github.com/dodWhatUp/install-modes-for-games'
    runtime_status = 'v031 historical partial live input; v05 pure tests only; host integration pending'
    exclusions = 'No game/mod/interpreter binaries, profiles, saves, credentials, private paths or raw logs'
    files = $taskRows
}
# Mechanical export only: writes new output, never source/settings/game files.
$taskUtf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $taskStage 'MANIFEST.json'), ($taskManifest | ConvertTo-Json -Depth 6), $taskUtf8)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$taskZip = Join-Path $taskOut 'GameInputModule-0.5-preview.1-2026-10-10.zip'
[IO.Compression.ZipFile]::CreateFromDirectory($taskStage, $taskZip, [IO.Compression.CompressionLevel]::Optimal, $false)
$taskArchive = [IO.Compression.ZipFile]::OpenRead($taskZip)
try {
    foreach ($taskRow in $taskRows) {
        $taskEntry = $taskArchive.GetEntry($taskRow.path)
        if (!$taskEntry) { throw "Archive missing entry: $($taskRow.path)" }
        $taskStream = $taskEntry.Open()
        $taskSha = [Security.Cryptography.SHA256]::Create()
        try { $taskActual = [BitConverter]::ToString($taskSha.ComputeHash($taskStream)).Replace('-', '') }
        finally { $taskStream.Dispose(); $taskSha.Dispose() }
        if ($taskActual -ne $taskRow.sha256) { throw "Archive integrity mismatch: $($taskRow.path)" }
    }
} finally { $taskArchive.Dispose() }
[ordered]@{ files = $taskRows.Count; archive = $taskZip; bytes = (Get-Item -LiteralPath $taskZip).Length;
    sha256 = (Get-FileHash -LiteralPath $taskZip -Algorithm SHA256).Hash } | ConvertTo-Json
