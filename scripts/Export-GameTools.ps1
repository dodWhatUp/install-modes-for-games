[CmdletBinding(DefaultParameterSetName = 'Export')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Export')][string]$OutputDirectory,
    [Parameter(ParameterSetName = 'Export')][ValidateSet('GameTools', 'GameInput')][string]$Bundle = 'GameTools',
    [Parameter(ParameterSetName = 'Export')][string]$ClientDate = '',
    [Parameter(Mandatory = $true, ParameterSetName = 'Library')][switch]$LibraryOnly
)
$ErrorActionPreference = 'Stop'

function Get-GameExportClientDate {
    # Client timezone, not the execution host's local timezone. The caller may
    # supply the explicit client date when exporting from another location.
    [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Israel Standard Time').ToString('yyyy-MM-dd')
}

function Get-GameSourcePaths {
    param([ValidateSet('GameTools', 'GameInput')][string]$Bundle)
    $inputPaths = @(
        'docs/AGENT-GAME-INPUT.md',
        'docs/GAME-TOOLS-ARCHITECTURE.md',
        'examples/game-input/README.md',
        'examples/game-input/GameInputModule.ahk',
        'examples/game-input/Start-GameInput.ahk',
        'examples/game-input/HostIntegration.example.ahk',
        'examples/game-input/AzeronOverlayStudio.integrated.ahk',
        'examples/game-input/OverlayStudioGameInput.ahk',
        'examples/game-input/OVERLAY-STUDIO-INTEGRATION.md',
        'examples/game-input/OTHER-CHAT-HANDOFF.txt',
        'examples/game-input/VALIDATION.json',
        'examples/game-input/baseline/ControlHelper-v031.ahk',
        'examples/skyrim-special-edition/Skyrim-F12-Test.ahk',
        'examples/skyrim-special-edition/README.md',
        'scripts/Export-GameInput.ps1',
        'scripts/Export-GameTools.ps1',
        'scripts/tests/Test-GameSourceExport.ps1'
    )
    if ($Bundle -eq 'GameInput') { return $inputPaths }
    $inputPaths + @(
        'AGENTS.md',
        'preferences/GENERAL.md',
        'docs/GAME-TOOLS-KNOWLEDGE-INDEX.md',
        'docs/KNOWLEDGE-MAINTENANCE.md',
        'docs/AUTOMATION-OPERATING-PROCEDURES.md',
        'docs/TOOL-RESOURCE-OVERHEAD.md',
        'docs/GAME-PERFORMANCE-MEASUREMENT.md',
        'docs/GAME-TOOL-CONNECTIONS.md',
        'docs/OPERATING-STANDARD.md',
        'docs/FEATURE-DECISION.md',
        'docs/AZERON-GAME-CONTROLS.md',
        'docs/INPUT-DEVICE-REGISTRY.md',
        'docs/GITHUB-PUBLISHING.md',
        'docs/DISTRIBUTION.md',
        'examples/game-tool-hub/README.md',
        'examples/game-tool-hub/Start-GameToolHub.ps1',
        'examples/game-tool-hub/form-draft.example.json',
        'examples/game-tool-hub/catalog.example.json',
        'scripts/Game-Tool-Hub.py',
        'scripts/Game-Tool-Catalog.py',
        'scripts/tests/Test-GameToolHub.py',
        'scripts/tests/Test-GameToolCatalog.py',
        'templates/AUTOMATION-TASK.example.json',
        'templates/KNOWLEDGE-RECORD.example.json',
        'templates/GAME-KEYBINDS.example.json',
        'templates/INPUT-DEVICE.example.json',
        'templates/PROFILE-MANIFEST.example.json',
        'templates/EXPERIMENT-LOG.md',
        'templates/GAME-HISTORY.md',
        'templates/MOD-CATALOG.md',
        'templates/OPTION-MENU.md',
        'templates/PREFERENCE-PROFILE.md'
    )
}

function Get-GameSourceHash {
    param([byte[]]$Bytes)
    $taskSha = [Security.Cryptography.SHA256]::Create()
    try { [BitConverter]::ToString($taskSha.ComputeHash($Bytes)).Replace('-', '') }
    finally { $taskSha.Dispose() }
}

function Assert-GameSourceCurrent {
    param([string]$RepositoryRoot, [object[]]$Plan)
    foreach ($taskEntry in $Plan) {
        $taskSource = Join-Path $RepositoryRoot $taskEntry.path
        if (!(Test-Path -LiteralPath $taskSource -PathType Leaf) -or
            (Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ne $taskEntry.sha256) {
            throw "Source changed since planning: $($taskEntry.path). Retain any partial checkpoint; it is not a current-source export."
        }
    }
}

function Assert-GameSourcePrivacy {
    param([string]$Text, [string]$Label)
    $taskPatterns = @(
        '[A-Za-z]:[\\/]+Users[\\/]+[^<>\\/\s]+[\\/]',
        'ghp_[A-Za-z0-9]{20,}',
        'github_pat_[A-Za-z0-9_]{20,}',
        'Bearer\s+[A-Za-z0-9._-]{25,}',
        '\bsk-[A-Za-z0-9_-]{20,}',
        '\bAKIA[A-Z0-9]{16}\b'
    )
    foreach ($taskPattern in $taskPatterns) {
        if ($Text -match $taskPattern) { throw "Review private-path/credential candidate: $Label" }
    }
}

function Assert-GameExportDestination {
    param([string]$RepositoryRoot, [string]$OutputDirectory)
    $taskRoot = [IO.Path]::GetFullPath($RepositoryRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $taskOutput = [IO.Path]::GetFullPath($OutputDirectory).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ($taskOutput.Equals($taskRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $taskOutput.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose a new output directory outside the repository.'
    }
    if (Test-Path -LiteralPath $taskOutput) { throw 'Output already exists. Choose a new directory; do not overwrite an earlier archive.' }
    # Fail closed on junction/symlink ancestors instead of writing through a
    # lexical outside-repository path into a different resolved target.
    $taskAncestor = Split-Path -Parent $taskOutput
    while ($taskAncestor) {
        if (Test-Path -LiteralPath $taskAncestor) {
            $taskItem = Get-Item -LiteralPath $taskAncestor -Force
            if (!$taskItem.PSIsContainer -or ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw 'Output ancestor is not an ordinary directory; choose a direct private output path.'
            }
        }
        $taskParent = Split-Path -Parent $taskAncestor
        if ($taskParent -eq $taskAncestor) { break }
        $taskAncestor = $taskParent
    }
    return $taskOutput
}

function Get-GameSourcePlan {
    param([string]$RepositoryRoot, [string[]]$RelativePaths)
    $taskRoot = [IO.Path]::GetFullPath($RepositoryRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $taskSeen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $taskAllowed = @('.md', '.txt', '.json', '.ps1', '.py', '.ahk')
    $taskUtf8 = [Text.UTF8Encoding]::new($false, $true)
    $taskPlan = @()
    foreach ($taskRelative in $RelativePaths) {
        if ($taskRelative -match '\\|(^|/)\.\.(/|$)' -or [IO.Path]::IsPathRooted($taskRelative) -or
            $taskRelative -notmatch '^[A-Za-z0-9_. /+-]+$' -or !$taskSeen.Add($taskRelative)) {
            throw "Invalid or duplicate source entry: $taskRelative"
        }
        if ([IO.Path]::GetExtension($taskRelative).ToLowerInvariant() -notin $taskAllowed) {
            throw "Unsupported source extension: $taskRelative"
        }
        $taskSource = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskRelative))
        if (!$taskSource.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
            !(Test-Path -LiteralPath $taskSource -PathType Leaf)) { throw "Missing or outside-repository source: $taskRelative" }
        $taskItem = Get-Item -LiteralPath $taskSource -Force
        # OneDrive placeholder directories carry ReparsePoint without redirect
        # targets. Reject actual links, not the cloud attribute by itself.
        if ($taskItem.LinkType -or $taskItem.Target -or $taskItem.Length -gt 2000000) {
            throw "Linked or oversized source: $taskRelative"
        }
        $taskAncestor = Split-Path -Parent $taskSource
        while (!$taskAncestor.Equals($taskRoot, [StringComparison]::OrdinalIgnoreCase)) {
            $taskAncestorItem = Get-Item -LiteralPath $taskAncestor -Force
            if ($taskAncestorItem.LinkType -or $taskAncestorItem.Target) {
                throw "Source ancestor is linked: $taskRelative"
            }
            $taskAncestor = Split-Path -Parent $taskAncestor
        }
        $taskBytes = [IO.File]::ReadAllBytes($taskSource)
        if ($taskBytes -contains 0) { throw "Binary/NUL source candidate: $taskRelative" }
        $taskText = $taskUtf8.GetString($taskBytes).TrimStart([char]0xFEFF)
        Assert-GameSourcePrivacy -Text $taskText -Label $taskRelative
        $taskHash = Get-GameSourceHash -Bytes $taskBytes
        if ($taskRelative -eq 'examples/game-input/baseline/ControlHelper-v031.ahk' -and
            $taskHash -ne 'EAFD9509DC8B7C579915668648AD20F000D377B5018B5ECE9D4CD9B43F7A46D8') {
            throw 'Historical baseline bytes differ; do not label this package byte-identical.'
        }
        # Capture bytes once; concurrent edits must not change a later copy
        # beneath a hash calculated from a different source revision.
        $taskPlan += [pscustomobject]@{ path=$taskRelative; bytes=$taskBytes.Length; sha256=$taskHash; content=$taskBytes; text=$taskText }
    }
    if ($taskPlan.Count -eq 0) { throw 'Empty source inventory.' }
    return $taskPlan
}

function Get-GameBundleMetadata {
    param([ValidateSet('GameTools', 'GameInput')][string]$Bundle, [object[]]$Plan, [string]$ClientDate)
    $taskDate = [DateTime]::MinValue
    if (![DateTime]::TryParseExact($ClientDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None, [ref]$taskDate)) { throw 'ClientDate must be an actual ISO date (yyyy-MM-dd).' }
    $taskValidationEntry = @($Plan | Where-Object path -eq 'examples/game-input/VALIDATION.json')
    if ($taskValidationEntry.Count -ne 1) { throw 'Exactly one input validation record is required.' }
    $taskValidation = $taskValidationEntry[0].text | ConvertFrom-Json
    $taskVersion = [string]$taskValidation.module_version
    if ($taskVersion -notmatch '^[0-9][A-Za-z0-9.+_-]{0,63}$') { throw 'Input module version is missing or unsafe.' }
    $taskModuleEntries = @($Plan | Where-Object path -eq 'examples/game-input/GameInputModule.ahk')
    if ($taskModuleEntries.Count -ne 1) { throw 'Exactly one input module source is required.' }
    $taskModuleVersions = [regex]::Matches($taskModuleEntries[0].text, 'Version:\s*"([0-9][A-Za-z0-9.+_-]{0,63})"')
    if ($taskModuleVersions.Count -ne 1 -or $taskModuleVersions[0].Groups[1].Value -ne $taskVersion) {
        throw 'Input source version disagrees with the validation record.'
    }
    $taskVersions = [ordered]@{ game_input=$taskVersion }
    if ($Bundle -eq 'GameTools') {
        foreach ($taskComponent in @(@{name='tool_hub';path='scripts/Game-Tool-Hub.py'}, @{name='tool_catalog';path='scripts/Game-Tool-Catalog.py'})) {
            $taskEntries = @($Plan | Where-Object path -eq $taskComponent.path)
            if ($taskEntries.Count -ne 1) { throw "Missing component version source: $($taskComponent.path)" }
            $taskMatches = [regex]::Matches($taskEntries[0].text, '(?m)^VERSION\s*=\s*"([0-9][A-Za-z0-9.+_-]{0,63})"\s*$')
            if ($taskMatches.Count -ne 1) { throw "Exactly one component VERSION is required: $($taskComponent.path)" }
            $taskVersions[$taskComponent.name] = $taskMatches[0].Groups[1].Value
        }
    }
    $taskArchiveName = if ($Bundle -eq 'GameInput') { "GameInputModule-$taskVersion-$ClientDate.zip" }
        else { "GameTools-input-$taskVersion-hub-$($taskVersions.tool_hub)-catalog-$($taskVersions.tool_catalog)-$ClientDate.zip" }
    return [ordered]@{
        schema_version=1; bundle=$Bundle; bundle_kind='authored-source-and-sanitized-knowledge-checkpoint'
        client_date=$ClientDate; client_timezone='Asia/Jerusalem'; component_versions=$taskVersions
        archive_name=$taskArchiveName; source='https://github.com/dodWhatUp/install-modes-for-games'
        source_state='Exact packaged file hashes; not claimed to match a published Git revision.'
        runtime_status='Historical v0.3.1 partial game input; current host has partial profile/picture observations. Current module lifecycle, game text/Unicode/Enter/Escape/hold acceptance remain pending. Export executes no runtime acceptance tests.'
        input_validation_reference='examples/game-input/VALIDATION.json'; input_recorded_date=$taskValidation.recorded_date
        input_declared_runtime=$taskValidation.preview_runtime
        exclusions=@('game/mod/interpreter binaries and archives', 'installed settings and picture assets', 'native/onboard/remapper profiles and device identities', 'Hub private registry and imported reports', 'saves, credentials, private paths and raw logs/video', 'unlisted sources and third-party SDK headers')
        recovery_boundary='Source restoration only, not full installed-tool/game/native-profile recovery. Private backups and supported runtimes are separate requirements. Restore/import acceptance is not established by archive integrity.'
    }
}

function Get-GameUnbundledReferences {
    param([string]$RepositoryRoot, [object[]]$Plan)
    $taskIncluded = @($Plan.path)
    $taskReferences = @()
    foreach ($taskEntry in $Plan) {
        if (!$taskEntry.path.EndsWith('.md')) { continue }
        foreach ($taskMatch in [regex]::Matches($taskEntry.text, '\]\(([^)\r\n]+)\)')) {
            $taskLink = $taskMatch.Groups[1].Value.Trim().Trim('<', '>')
            if ($taskLink -match '^([A-Za-z][A-Za-z0-9+.-]*:|#)' -or $taskLink -match '\s') { continue }
            $taskLinkPath = [Uri]::UnescapeDataString(($taskLink -split '[?#]', 2)[0])
            if ($taskLinkPath -eq '') { continue }
            $taskResolved = [IO.Path]::GetFullPath((Join-Path (Split-Path -Parent (Join-Path $RepositoryRoot $taskEntry.path)) $taskLinkPath))
            if (!$taskResolved.StartsWith($RepositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Markdown reference leaves repository: $($taskEntry.path)"
            }
            $taskRelative = $taskResolved.Substring($RepositoryRoot.Length + 1).Replace('\', '/')
            if ($taskRelative -notin $taskIncluded) {
                $taskReferences += [ordered]@{ from=$taskEntry.path; reference=$taskLink; excluded_source=$taskRelative
                    canonical_source='https://github.com/dodWhatUp/install-modes-for-games/blob/main/' + (($taskRelative -split '/' | ForEach-Object { [Uri]::EscapeDataString($_) }) -join '/')
                    exists_in_checkout=(Test-Path -LiteralPath $taskResolved); note='Not bundled; link does not prove publication, access or runtime acceptance.' }
            }
        }
    }
    return $taskReferences
}

function Invoke-GameSourceExport {
    param([string]$RepositoryRoot, [string]$OutputDirectory, [object[]]$Plan, [Collections.IDictionary]$Metadata)
    $taskRoot = [IO.Path]::GetFullPath($RepositoryRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if ([string]$Metadata.archive_name -notmatch '^[A-Za-z0-9][A-Za-z0-9.+_-]{0,180}\.zip$') {
        throw 'Archive name must be a safe ZIP leaf name.'
    }
    $taskOutput = Assert-GameExportDestination -RepositoryRoot $taskRoot -OutputDirectory $OutputDirectory
    $taskManifest = [ordered]@{}
    foreach ($taskKey in $Metadata.Keys) { $taskManifest[$taskKey] = $Metadata[$taskKey] }
    $taskManifest.created_utc = [DateTime]::UtcNow.ToString('o')
    $taskManifest.source_consistency_policy = 'Source hashes checked before output mutation and again after archive verification. Any mismatch refuses a successful current-source receipt; an already-created checkpoint is retained, not overwritten.'
    $taskManifest.files = @($Plan | ForEach-Object { [ordered]@{path=$_.path;bytes=$_.bytes;sha256=$_.sha256} })
    $taskManifest.unbundled_references = @(Get-GameUnbundledReferences -RepositoryRoot $taskRoot -Plan $Plan)
    $taskManifest.privacy_review = 'Curated inventory and limited pattern scan; manual content/privacy review remains required before publication.'
    $taskUtf8 = [Text.UTF8Encoding]::new($false)
    $taskManifestBytes = $taskUtf8.GetBytes(($taskManifest | ConvertTo-Json -Depth 16))
    Assert-GameSourcePrivacy -Text $taskUtf8.GetString($taskManifestBytes) -Label 'generated manifest'
    Assert-GameSourceCurrent -RepositoryRoot $taskRoot -Plan $Plan
    $null = Assert-GameExportDestination -RepositoryRoot $taskRoot -OutputDirectory $taskOutput
    New-Item -ItemType Directory -Path $taskOutput | Out-Null
    $taskStage = Join-Path $taskOutput 'source'
    New-Item -ItemType Directory -Path $taskStage | Out-Null
    foreach ($taskEntry in $Plan) {
        $taskDestination = Join-Path $taskStage $taskEntry.path
        New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
        [IO.File]::WriteAllBytes($taskDestination, $taskEntry.content)
    }
    [IO.File]::WriteAllBytes((Join-Path $taskStage 'MANIFEST.json'), $taskManifestBytes)
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $taskZip = Join-Path $taskOutput $Metadata.archive_name
    # .NET Framework's CreateFromDirectory can emit Windows backslash entry
    # names. Explicit CreateEntry names preserve portable forward-slash paths
    # in both Windows PowerShell 5.1 and PowerShell 7/.NET.
    $taskZipRows = @($Plan | ForEach-Object { [pscustomobject]@{path=$_.path;content=$_.content} }) +
        @([pscustomobject]@{path='MANIFEST.json';content=$taskManifestBytes})
    $taskZipStream = [IO.File]::Open($taskZip, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $taskZipWriter = $null
    try {
        $taskZipWriter = [IO.Compression.ZipArchive]::new($taskZipStream, [IO.Compression.ZipArchiveMode]::Create, $false)
        foreach ($taskZipRow in $taskZipRows) {
            $taskWriteEntry = $taskZipWriter.CreateEntry($taskZipRow.path, [IO.Compression.CompressionLevel]::Optimal)
            $taskWriteStream = $taskWriteEntry.Open()
            try {
                $taskWriteBytes = [byte[]]$taskZipRow.content
                $taskWriteStream.Write($taskWriteBytes, 0, $taskWriteBytes.Length)
            } finally { $taskWriteStream.Dispose() }
        }
    } finally {
        if ($taskZipWriter) { $taskZipWriter.Dispose() }
        $taskZipStream.Dispose()
    }
    $taskExpected = @($taskManifest.files) + @([ordered]@{path='MANIFEST.json';bytes=$taskManifestBytes.Length;sha256=(Get-GameSourceHash -Bytes $taskManifestBytes)})
    $taskArchive = [IO.Compression.ZipFile]::OpenRead($taskZip)
    try {
        $taskNames = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        foreach ($taskEntry in $taskArchive.Entries) {
            if ($taskEntry.FullName.Contains('\')) { throw 'Archive contains a nonportable backslash entry name.' }
            if (!$taskNames.Add($taskEntry.FullName)) { throw 'Duplicate archive entry.' }
        }
        if ($taskArchive.Entries.Count -ne $taskExpected.Count) { throw 'Unexpected archive inventory.' }
        foreach ($taskRow in $taskExpected) {
            $taskEntry = $taskArchive.GetEntry($taskRow.path)
            if (!$taskEntry -or $taskEntry.Length -ne $taskRow.bytes) { throw "Archive missing or wrong-size entry: $($taskRow.path)" }
            $taskStream = $taskEntry.Open()
            $taskSha = [Security.Cryptography.SHA256]::Create()
            try { $taskActual = [BitConverter]::ToString($taskSha.ComputeHash($taskStream)).Replace('-', '') }
            finally { $taskStream.Dispose(); $taskSha.Dispose() }
            if ($taskActual -ne $taskRow.sha256) { throw "Archive integrity mismatch: $($taskRow.path)" }
        }
    } finally { $taskArchive.Dispose() }
    Assert-GameSourceCurrent -RepositoryRoot $taskRoot -Plan $Plan
    return [ordered]@{files=$Plan.Count;archive=$taskZip;bytes=(Get-Item -LiteralPath $taskZip).Length
        sha256=(Get-FileHash -LiteralPath $taskZip -Algorithm SHA256).Hash;manifest_sha256=(Get-GameSourceHash -Bytes $taskManifestBytes)
        integrity='all_source_and_manifest_zip_entries_verified';source_current_at_final_hash_check=$true;source_checked_utc=[DateTime]::UtcNow.ToString('o')
        recovery='source_checkpoint_not_full_recovery'}
}

if (!$LibraryOnly) {
    $taskRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    if ($ClientDate -eq '') { $ClientDate = Get-GameExportClientDate }
    $taskPlan = Get-GameSourcePlan -RepositoryRoot $taskRepository -RelativePaths (Get-GameSourcePaths -Bundle $Bundle)
    $taskMetadata = Get-GameBundleMetadata -Bundle $Bundle -Plan $taskPlan -ClientDate $ClientDate
    Invoke-GameSourceExport -RepositoryRoot $taskRepository -OutputDirectory $OutputDirectory -Plan $taskPlan -Metadata $taskMetadata |
        ConvertTo-Json -Depth 8
}
