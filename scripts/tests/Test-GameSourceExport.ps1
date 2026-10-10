$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\Export-GameTools.ps1') -LibraryOnly
$testCount = 0
function Assert-ExportTest {
    param([bool]$Condition, [string]$Name)
    if (!$Condition) { throw "FAIL: $Name" }
    $script:testCount += 1
}
function Assert-ExportRefusal {
    param([scriptblock]$Action, [string]$Expected, [string]$Name)
    $testError = ''
    try { $null = & $Action } catch { $testError = $_.Exception.Message }
    Assert-ExportTest -Condition ($testError.Length -gt 0 -and $testError -like "*$Expected*") -Name $Name
}
function Write-ExportFixture {
    param([string]$Relative, [string]$Text)
    $testFile = Join-Path $testRepo $Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $testFile) -Force | Out-Null
    [IO.File]::WriteAllText($testFile, $Text, [Text.UTF8Encoding]::new($false))
}
$testTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
$testRoot = Join-Path $testTemp ('GameToolsExportTest-' + [Guid]::NewGuid().ToString('N'))
$testRepo = Join-Path $testRoot 'repository'
New-Item -ItemType Directory -Path $testRepo | Out-Null
try {
    Write-ExportFixture 'docs/source.md' '# Fixture with [excluded](../other.md)'
    Write-ExportFixture 'other.md' 'Referenced, intentionally not included.'
    $testValidation = '{"module_version":"0.5-preview.3","recorded_date":"2026-10-11","preview_runtime":{"game_receipt":"pending"}}'
    Write-ExportFixture 'examples/game-input/VALIDATION.json' $testValidation
    Write-ExportFixture 'examples/game-input/GameInputModule.ahk' 'Version: "0.5-preview.3"'
    Write-ExportFixture 'scripts/Game-Tool-Hub.py' 'VERSION = "0.2.0"'
    Write-ExportFixture 'scripts/Game-Tool-Catalog.py' 'VERSION = "0.1.0"'
    $testPaths = @('docs/source.md', 'examples/game-input/VALIDATION.json', 'scripts/Game-Tool-Hub.py', 'scripts/Game-Tool-Catalog.py', 'examples/game-input/GameInputModule.ahk')
    $testPlan = @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths $testPaths)
    Assert-ExportTest ($testPlan.Count -eq 5) 'exact fixture inventory'
    Assert-ExportTest ($testPlan[0].sha256 -eq (Get-FileHash -LiteralPath (Join-Path $testRepo 'docs/source.md')).Hash) 'source hash matches bytes'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('docs/source.md','DOCS/SOURCE.md') } 'duplicate' 'case-insensitive duplicate refusal'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('missing.md') } 'Missing' 'missing source refusal'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('game.dll') } 'Unsupported' 'binary extension refusal'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('../other.md') } 'Invalid' 'source traversal refusal'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @() } 'Empty' 'empty inventory refusal'
    Write-ExportFixture 'binary.txt' ([string][char]0)
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('binary.txt') } 'Binary' 'NUL text refusal'
    [IO.File]::WriteAllBytes((Join-Path $testRepo 'invalid.txt'), [byte[]]@(255,255))
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('invalid.txt') } '' 'invalid UTF-8 refusal'
    $testPrivatePath = 'C:' + [char]92 + 'Users' + [char]92 + 'example-person' + [char]92 + 'private.txt'
    Assert-ExportRefusal { Assert-GameSourcePrivacy -Text $testPrivatePath -Label fixture } 'private-path' 'private path refusal'
    foreach ($testCredential in @(
        ('gh' + 'p_' + ('x' * 24)), ('github_' + 'pat_' + ('x' * 24)),
        ('Bear' + 'er ' + ('x' * 30)), ('s' + 'k-' + ('x' * 24)), ('AK' + 'IA' + ('A' * 16)))) {
        Assert-ExportRefusal { Assert-GameSourcePrivacy -Text $testCredential -Label fixture } 'credential' 'credential candidate refusal'
    }
    Write-ExportFixture 'examples/game-input/baseline/ControlHelper-v031.ahk' 'Not the immutable baseline.'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('examples/game-input/baseline/ControlHelper-v031.ahk') } 'baseline bytes' 'baseline mutation refusal'
    Assert-ExportRefusal { Assert-GameExportDestination -RepositoryRoot $testRepo -OutputDirectory $testRepo } 'outside' 'repository-root output refusal'
    Assert-ExportRefusal { Assert-GameExportDestination -RepositoryRoot $testRepo -OutputDirectory (Join-Path $testRepo 'out') } 'outside' 'in-repository output refusal'
    Assert-ExportRefusal { Assert-GameExportDestination -RepositoryRoot $testRepo -OutputDirectory $testRoot } 'exists' 'preexisting output refusal'
    $testMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testMetadata.component_versions.game_input -eq '0.5-preview.3' -and $testMetadata.component_versions.tool_catalog -eq '0.1.0') 'versions taken from fixture sources'
    Assert-ExportTest ($testMetadata.archive_name -like '*2026-10-11.zip') 'explicit client date in filename'
    Assert-ExportTest ($testMetadata.recovery_boundary -like '*not full*' -and $testMetadata.runtime_status -like '*pending*') 'truthful recovery and runtime boundaries'
    Assert-ExportRefusal { Get-GameBundleMetadata -Bundle GameTools -Plan $testPlan -ClientDate '2026-02-30' } 'actual ISO date' 'invalid calendar date refusal'
    $testMixedPlan = @($testPlan | ForEach-Object { $_.PSObject.Copy() })
    $testMixedPlan[-1].text = 'Version: "0.5-preview.4"'
    Assert-ExportRefusal { Get-GameBundleMetadata -Bundle GameTools -Plan $testMixedPlan -ClientDate '2026-10-11' } 'disagrees' 'source and validation version mismatch refusal'
    $testUnsafeMetadata = [ordered]@{archive_name='../escape.zip'}
    Assert-ExportRefusal { Invoke-GameSourceExport -RepositoryRoot $testRepo -OutputDirectory (Join-Path $testRoot 'unsafe') -Plan $testPlan -Metadata $testUnsafeMetadata } 'safe ZIP leaf' 'archive traversal refusal'
    $testReferences = @(Get-GameUnbundledReferences -RepositoryRoot $testRepo -Plan $testPlan)
    Assert-ExportTest ($testReferences.Count -eq 1 -and $testReferences[0].excluded_source -eq 'other.md') 'unbundled canonical reference declared'
    # Snapshot immutability: a source change after planning must not be packaged
    # beneath a hash from a different revision.
    Write-ExportFixture 'docs/source.md' 'Newer concurrent fixture revision.'
    Assert-ExportRefusal { Invoke-GameSourceExport -RepositoryRoot $testRepo -OutputDirectory (Join-Path $testRoot 'stale') -Plan $testPlan -Metadata $testMetadata } 'Source changed' 'stale planned-source export refusal'
    Assert-ExportTest (!(Test-Path -LiteralPath (Join-Path $testRoot 'stale'))) 'stale source refused before output mutation'
    [IO.File]::WriteAllBytes((Join-Path $testRepo 'docs/source.md'), $testPlan[0].content)
    $testReceipt = Invoke-GameSourceExport -RepositoryRoot $testRepo -OutputDirectory (Join-Path $testRoot 'export') -Plan $testPlan -Metadata $testMetadata
    Assert-ExportTest ($testReceipt.files -eq 5 -and $testReceipt.integrity -eq 'all_source_and_manifest_zip_entries_verified') 'fixture archive fully verified'
    Assert-ExportTest ($testReceipt.sha256 -eq (Get-FileHash -LiteralPath $testReceipt.archive).Hash) 'archive receipt hash'
    $testArchive = [IO.Compression.ZipFile]::OpenRead($testReceipt.archive)
    try {
        Assert-ExportTest (@($testArchive.Entries | Where-Object { $_.FullName.Contains('\') }).Count -eq 0 -and
            $null -ne $testArchive.GetEntry('docs/source.md')) 'portable forward-slash archive entries'
    } finally { $testArchive.Dispose() }
    Assert-ExportTest $testReceipt.source_current_at_final_hash_check 'final source hash verification reported'
    $testStaged = Join-Path $testRoot 'export\source\docs\source.md'
    Assert-ExportTest ((Get-FileHash -LiteralPath $testStaged).Hash -eq $testPlan[0].sha256) 'original planned bytes preserved'
    $testManifest = Get-Content -LiteralPath (Join-Path $testRoot 'export\source\MANIFEST.json') -Raw | ConvertFrom-Json
    Assert-ExportTest ($testManifest.files.Count -eq 5 -and $testManifest.input_declared_runtime.game_receipt -eq 'pending') 'manifest exact sources and pending evidence'
    Assert-ExportRefusal { Invoke-GameSourceExport -RepositoryRoot $testRepo -OutputDirectory (Join-Path $testRoot 'export') -Plan $testPlan -Metadata $testMetadata } 'exists' 'repeat export cannot overwrite'
    $testInputPaths = @(Get-GameSourcePaths -Bundle GameInput)
    $testAllPaths = @(Get-GameSourcePaths -Bundle GameTools)
    Assert-ExportTest ($testInputPaths -contains 'examples/game-input/AzeronOverlayStudio.integrated.ahk' -and $testInputPaths -contains 'examples/game-input/OverlayStudioGameInput.ahk') 'input integration source inventory'
    Assert-ExportTest ($testAllPaths -contains 'templates/AUTOMATION-TASK.example.json' -and $testAllPaths -contains 'scripts/tests/Test-GameToolCatalog.py') 'combined curated inventory'
    Assert-ExportTest ($testAllPaths -contains 'docs/KNOWLEDGE-MAINTENANCE.md' -and $testAllPaths -contains 'templates/KNOWLEDGE-RECORD.example.json') 'knowledge maintenance and lesson inventory'
    Assert-ExportTest ($testInputPaths -notcontains 'templates/KNOWLEDGE-RECORD.example.json' -and $testInputPaths -notcontains 'docs/KNOWLEDGE-MAINTENANCE.md') 'knowledge additions do not widen input-only bundle'
    Assert-ExportTest (@($testAllPaths | Sort-Object -Unique).Count -eq $testAllPaths.Count) 'curated inventory has no duplicates'
    "PASS: $testCount source-export contracts; temporary synthetic fixtures only, no app/game/input/capture or upload."
} finally {
    # Remove only this exact generated fixture tree after absolute target checks.
    $testResolved = [IO.Path]::GetFullPath($testRoot)
    if (!$testResolved.StartsWith($testTemp + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path -Leaf $testResolved) -notmatch '^GameToolsExportTest-[a-f0-9]{32}$') {
        throw 'Fixture cleanup target did not pass containment validation.'
    }
    if (Test-Path -LiteralPath $testResolved) { Remove-Item -LiteralPath $testResolved -Recurse -Force }
}
