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
    Write-ExportFixture 'scripts/Start-UnifiedTools.pyw' '# Inert stable launcher fixture'
    Assert-ExportTest (@(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('scripts/Start-UnifiedTools.pyw')).Count -eq 1) 'authored windowed Python launcher is retained as source'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('../other.md') } 'Invalid' 'source traversal refusal'
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @() } 'Empty' 'empty inventory refusal'
    Write-ExportFixture 'binary.txt' ([string][char]0)
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('binary.txt') } 'Binary' 'NUL text refusal'
    [IO.File]::WriteAllBytes((Join-Path $testRepo 'invalid.txt'), [byte[]]@(255,255))
    Assert-ExportRefusal { Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('invalid.txt') } '' 'invalid UTF-8 refusal'
    $testPrivatePath = 'C:' + [char]92 + 'Users' + [char]92 + 'example-person' + [char]92 + 'private.txt'
    Assert-ExportRefusal { Assert-GameSourcePrivacy -Text $testPrivatePath -Label fixture } 'private-path' 'private path refusal'
    Assert-GameSourcePrivacy -Text 'C:/Users/Public/Documents/reWASD/Profiles' -Label 'public system folder'
    Assert-ExportTest $true 'public Windows folder is not a personal path'
    Assert-ExportRefusal { Assert-GameSourcePrivacy -Text ($testPrivatePath.Replace('example-person', 'Public-person')) -Label fixture } 'private-path' 'public prefix does not exempt personal accounts'
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
    $testCanonicalRevision = '043f3c4733788f082da98dfcb43c0972d2794c6a'
    Assert-ExportRefusal { Get-GameUnbundledReferences -RepositoryRoot $testRepo -Plan $testPlan } 'exact canonical reference revision' 'unbundled reference requires exact revision'
    $testReferences = @(Get-GameUnbundledReferences -RepositoryRoot $testRepo -Plan $testPlan -CanonicalRevision $testCanonicalRevision)
    Assert-ExportTest ($testReferences.Count -eq 1 -and $testReferences[0].excluded_source -eq 'other.md' -and
        $testReferences[0].canonical_revision -eq $testCanonicalRevision) 'unbundled canonical reference declared and pinned'
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
    Assert-ExportTest ($testAllPaths -contains 'docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md' -and $testInputPaths -notcontains 'docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md') 'adopted Azeron keymap viewer owner document only in combined inventory'
    Assert-ExportTest ($testAllPaths -contains 'templates/AUTOMATION-TASK.example.json' -and $testAllPaths -contains 'scripts/tests/Test-GameToolCatalog.py') 'combined curated inventory'
    Assert-ExportTest ($testAllPaths -contains 'docs/KNOWLEDGE-MAINTENANCE.md' -and $testAllPaths -contains 'templates/KNOWLEDGE-RECORD.example.json') 'knowledge maintenance and lesson inventory'
    $testAIAcceptancePaths = @(
        'docs/AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md',
        'docs/AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json',
        'docs/AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.md',
        'docs/AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.json')
    Assert-ExportTest (@($testAIAcceptancePaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'AI Windows acceptance and canonical reconciliation only in combined inventory'
    Assert-ExportTest ($testAllPaths -contains 'scripts/tests/requirements.txt' -and $testInputPaths -notcontains 'scripts/tests/requirements.txt') 'test-only dependency inventory'
    Assert-ExportTest ($testAllPaths -contains 'scripts/tests/GameToolAITestPackage.py' -and $testInputPaths -notcontains 'scripts/tests/GameToolAITestPackage.py') 'AI source-checkout package fixture inventory'
    $testPlanningPaths = @('docs/AI-PLANNING-READONLY-SLICE.md', 'docs/AI-PLANNING-READONLY-VALIDATION.json',
        'schemas/game-tools-goal-plan.schema.json',
        'scripts/GameToolInstances.py', 'scripts/GameToolPlanning.py', 'scripts/Game-Instances.py',
        'scripts/tests/Test-GameToolPlanning.py')
    Assert-ExportTest (@($testPlanningPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'read-only planning, opaque instances and UMM adapter only in combined inventory'
    Assert-ExportTest ($testAllPaths -contains 'scripts/GameToolKeybindIntegration.py' -and $testAllPaths -contains 'scripts/game_keybind_ops/core.py' -and $testAllPaths -contains 'schemas/game-pack.schema.json' -and $testAllPaths -contains 'scripts/tests/Test-GameToolKeybindMerge.py') 'merged keybind source, schema and conflict tests inventory'
    Assert-ExportTest ($testAllPaths -contains 'scripts/GameToolCatalogBridge.py' -and $testAllPaths -contains 'scripts/GameToolCatalogPanel.py' -and $testAllPaths -contains 'scripts/tests/Test-GameToolHubCatalog.py') 'shared catalog GUI integration inventory'
    Assert-ExportTest ($testAllPaths -contains 'scripts/GameFgInspector.py' -and $testAllPaths -contains 'scripts/GameFgPreflight.py' -and $testAllPaths -contains 'scripts/tests/test_game_fg_inspector.py' -and $testAllPaths -contains 'scripts/tests/test_game_fg_preflight.py') 'read-only FG preflight modules and fixture inventory'
    $testComparisonPaths = @('docs/GAME-TOOLS-MASTER-CHECKLIST.md', 'docs/GAME-TELEMETRY-TOOL-PLAN.md', 'docs/OFFLINE-COMPARISON-REPORTS.md',
        'examples/game-tool-hub/COMPARISON-DATASET.md', 'examples/game-tool-hub/comparison-fixture.example.json',
        'scripts/GameToolComparison.py', 'scripts/GameToolComparisonPanel.py',
        'scripts/tests/Test-GameToolComparison.py', 'scripts/tests/Test-GameToolComparisonPanel.py',
        'scripts/tests/Test-GameToolComparisonCLI.py')
    Assert-ExportTest (@($testComparisonPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'offline comparison sources and checklist only in combined inventory'
    $testImportPaths = @('scripts/GameToolReportImport.py', 'scripts/tests/Test-GameToolReportImport.py',
        'scripts/tests/Test-GameToolReportImportPanel.py', 'scripts/tests/Test-GameToolReportImportCLI.py',
        'examples/game-tool-hub/import-fixtures/cyberpunk-summary.example.json',
        'examples/game-tool-hub/import-fixtures/presentmon-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-no-animation-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-zero-stats.example.csv')
    Assert-ExportTest (@($testImportPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'saved-summary adapters and authored format fixtures only in combined inventory'
    $testCoordinationPaths = @('scripts/GameToolJournal.py', 'scripts/GameToolCoordinator.py',
        'scripts/GameToolSessionPanel.py', 'scripts/tests/Test-GameToolJournal.py',
        'scripts/tests/Test-GameToolCoordinator.py', 'scripts/tests/Test-GameToolSessionPanel.py',
        'scripts/tests/Test-GameToolSessionCLI.py')
    Assert-ExportTest (@($testCoordinationPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'offline coordination and journal sources only in combined inventory'
    $testCoordinationPlan = @($testPlan)
    foreach ($testComponentName in @('Coordinator', 'Journal', 'SessionPanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testCoordinationPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testCoordinationMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testCoordinationPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testCoordinationMetadata.component_versions.coordinator -eq '0.1.0' -and
        $testCoordinationMetadata.component_versions.journal -eq '0.1.0' -and
        $testCoordinationMetadata.component_versions.session_panel -eq '0.1.0') 'optional coordination versions captured from exact source bytes'
    Assert-ExportTest ($testInputPaths -notcontains 'templates/KNOWLEDGE-RECORD.example.json' -and $testInputPaths -notcontains 'docs/KNOWLEDGE-MAINTENANCE.md') 'knowledge additions do not widen input-only bundle'
    $testEvidencePaths = @('scripts/GameToolCrashEvidence.py', 'scripts/GameToolEvidencePanel.py',
        'scripts/tests/Test-GameToolCrashEvidence.py', 'scripts/tests/Test-GameToolEvidencePanel.py',
        'scripts/tests/Test-GameToolEvidenceCLI.py')
    Assert-ExportTest (@($testEvidencePaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'saved evidence sources only in combined inventory'
    $testEvidencePlan = @($testCoordinationPlan)
    foreach ($testComponentName in @('CrashEvidence', 'EvidencePanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testEvidencePlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testEvidenceMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testEvidencePlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testEvidenceMetadata.component_versions.crash_evidence -eq '0.1.0' -and
        $testEvidenceMetadata.component_versions.evidence_panel -eq '0.1.0') 'saved evidence versions captured from exact source bytes'
    $testWorkflowPaths = @('scripts/GameToolWorkflow.py', 'scripts/GameToolWorkflowPanel.py',
        'scripts/tests/Test-GameToolWorkflow.py', 'scripts/tests/Test-GameToolWorkflowPanel.py',
        'scripts/tests/Test-GameToolWorkflowCLI.py', 'examples/game-tool-hub/workflow-installation.example.json',
        'examples/game-tool-hub/workflow-diagnostic.example.json')
    Assert-ExportTest (@($testWorkflowPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'data-only workflows only in combined source inventory'
    $testWorkflowPlan = @($testEvidencePlan)
    foreach ($testComponentName in @('Workflow', 'WorkflowPanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testWorkflowPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testWorkflowMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testWorkflowPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testWorkflowMetadata.component_versions.workflow -eq '0.1.0' -and
        $testWorkflowMetadata.component_versions.workflow_panel -eq '0.1.0') 'workflow versions from exact source bytes'
    $testReadinessPaths = @('scripts/GameToolReadiness.py','scripts/GameToolReadinessPanel.py',
        'scripts/tests/Test-GameToolReadiness.py','scripts/tests/Test-GameToolReadinessPanel.py',
        'scripts/tests/Test-GameToolReadinessCLI.py','examples/game-tool-hub/provider-health.example.json',
        'examples/game-tool-hub/scenario.example.json')
    Assert-ExportTest (@($testReadinessPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'offline readiness sources only in combined source allowlist'
    $testReadinessPlan = @($testWorkflowPlan)
    foreach ($testComponentName in @('Readiness','ReadinessPanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testReadinessPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testReadinessMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testReadinessPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testReadinessMetadata.component_versions.readiness -eq '0.1.0' -and $testReadinessMetadata.component_versions.readiness_panel -eq '0.1.0') 'readiness versions from exact source bytes'
    $testOverlayPaths = @('scripts/GameToolOverlay.py','scripts/GameToolOverlayPanel.py','scripts/GameToolCompactUI.py',
        'scripts/GameToolAzeronLayer.py','scripts/tests/Test-GameToolAzeronLayer.py',
        'scripts/Build-OverlayContract.py','scripts/Install-GameToolsRelease.ps1','scripts/tests/Test-GameToolOverlay.py',
        'scripts/tests/Test-GameToolsInstaller.py','docs/OVERLAY-GROUPS.md','examples/game-tool-hub/overlay-manifest.example.json')
    Assert-ExportTest (@($testOverlayPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'overlay source/contracts only in combined inventory'
    Assert-ExportTest ($testInputPaths -contains 'examples/game-input/StudioOverlayGroups.ahk' -and
        $testInputPaths -contains 'examples/game-input/tests/Test-OverlayGroups.ahk') 'optional AHK display adapter retained in input source bundle'
    $testOverlayPlan = @($testReadinessPlan)
    foreach ($testComponentName in @('Overlay','OverlayPanel','CompactUI')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testOverlayPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testOverlayMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testOverlayPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testOverlayMetadata.component_versions.overlay -eq '0.1.0' -and $testOverlayMetadata.component_versions.overlay_panel -eq '0.1.0' -and
        $testOverlayMetadata.component_versions.compact_ui -eq '0.1.0') 'overlay versions pinned to exact source bytes'
    Write-ExportFixture 'scripts/GameToolOverlayAlternateUI.py' "VERSION = '0.1.1'"
    $testSingleQuotePlan = @($testOverlayPlan) + @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('scripts/GameToolOverlayAlternateUI.py'))
    $testSingleQuoteMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testSingleQuotePlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testSingleQuoteMetadata.component_versions.overlay_alternate_ui -eq '0.1.1') 'Python single quoted component version preserved'
    Write-ExportFixture 'examples/game-input/AzeronOverlayStudio.integrated.ahk' 'this.Version := "2.2.0-groups-preview.1"'
    $testOverlayPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('examples/game-input/AzeronOverlayStudio.integrated.ahk'))
    $testStudioMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testOverlayPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testStudioMetadata.component_versions.overlay_studio -eq '2.2.0-groups-preview.1') 'optional Studio version comes from exact authored host source'
    Write-ExportFixture 'examples/game-input/AzeronOverlayStudio.integrated.ahk' 'this.Version := "2.2.0-unified.1"'
    $testUnifiedPlan = @($testOverlayPlan | Where-Object path -ne 'examples/game-input/AzeronOverlayStudio.integrated.ahk')
    $testUnifiedPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @('examples/game-input/AzeronOverlayStudio.integrated.ahk'))
    foreach ($testComponentName in @('Unified','UnifiedPanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testUnifiedPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testUnifiedMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testUnifiedPlan -ClientDate '2026-10-11'
    Assert-ExportTest ($testUnifiedMetadata.component_versions.overlay_studio -eq '2.2.0-unified.1' -and
        $testUnifiedMetadata.component_versions.unified -eq '0.1.0' -and $testUnifiedMetadata.component_versions.unified_panel -eq '0.1.0') 'unified host and updater versions come from captured sources'
    $testDataPaths = @('scripts/GameToolWorkspace.py','scripts/GameToolUserData.py','scripts/GameToolUserDataPanel.py',
        'scripts/tests/Test-GameToolWorkspace.py','scripts/tests/Test-GameToolUserData.py','scripts/tests/Test-GameToolUserDataPanel.py')
    Assert-ExportTest (@($testDataPaths | Where-Object { $testAllPaths -notcontains $_ -or $testInputPaths -contains $_ }).Count -eq 0) 'goal navigation and private data compatibility only in combined bundle'
    Assert-ExportTest ($testAllPaths -contains 'scripts/tests/Test-GameToolCompactUI.py' -and $testInputPaths -notcontains 'scripts/tests/Test-GameToolCompactUI.py') 'shared compact controls and scroll ownership regression included in combined bundle'
    foreach ($testComponentName in @('Workspace','UserData','UserDataPanel')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testUnifiedPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testLayerMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testUnifiedPlan -ClientDate '2026-10-12'
    Assert-ExportTest ($testLayerMetadata.component_versions.workspace -eq '0.1.0' -and
        $testLayerMetadata.component_versions.user_data -eq '0.1.0' -and $testLayerMetadata.component_versions.user_data_panel -eq '0.1.0') 'layer versions captured separately from data/schema versions'
    foreach ($testComponentName in @('Instances','Planning')) {
        $testComponentPath = 'scripts/GameTool' + $testComponentName + '.py'
        Write-ExportFixture $testComponentPath 'VERSION = "0.1.0"'
        $testUnifiedPlan += @(Get-GameSourcePlan -RepositoryRoot $testRepo -RelativePaths @($testComponentPath))
    }
    $testPlanningMetadata = Get-GameBundleMetadata -Bundle GameTools -Plan $testUnifiedPlan -ClientDate '2026-10-12'
    Assert-ExportTest ($testPlanningMetadata.component_versions.instances -eq '0.1.0' -and
        $testPlanningMetadata.component_versions.planning -eq '0.1.0') 'instance and planning versions captured from exact source bytes'
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
