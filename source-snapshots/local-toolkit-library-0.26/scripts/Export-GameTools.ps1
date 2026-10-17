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
        'examples/game-input/StudioPictureModule.ahk',
        'examples/game-input/StudioOverlayGroups.ahk',
        'examples/game-input/StudioHubBridge.ahk',
        'examples/game-input/tests/Test-OverlayGroups.ahk',
        'examples/game-input/tests/Test-UIFeedback.ahk',
        'examples/game-input/tests/Test-PictureModule.ahk',
        'examples/game-input/tests/Test-PictureEditor.ahk',
        'examples/game-input/tests/Test-MicEditor.ahk',
        'scripts/tests/Test-PictureHost.py',
        'scripts/tests/Run-NativePictureDesktop.py',
        'scripts/tests/Test-NativePictureLayout.py',
        'scripts/tests/Test-ModernStartup.py',
        'examples/game-input/PICTURE-BUTTONS.md',
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
    $mergedPaths = @(
        '00_START_HERE.html',
        'AGENTS.md',
        'CHECKPOINT.md',
        'KEYBIND_INTEGRATION_HANDOFF.md',
        'OPENING_MESSAGE_HE.txt',
        'Open-Keybinds.cmd',
        'README.md',
        'docs/AGENT-GAME-INPUT.md',
        'docs/AUTOMATION-OPERATING-PROCEDURES.md',
        'docs/AZERON-GAME-CONTROLS.md',
        'docs/DEPENDENCY_PINS.json',
        'docs/DISTRIBUTION.md',
        'docs/EXTENSION_GUIDE.md',
        'docs/FEATURE-DECISION.md',
        'docs/FOCUS-UI-PRIOR-ARTIFACTS.json',
        'docs/FOCUS-UI-REVIEW.md',
        'docs/FOCUS-UI-SOURCE-DELTA.json',
        'docs/FOCUS-UI-VALIDATION.json',
        'docs/GAME-PERFORMANCE-MEASUREMENT.md',
        'docs/GAME-SUPPORT-PACKS.md',
        'docs/GAME-SUPPORT-SOURCE-DELTA.json',
        'docs/GAME-SUPPORT-VALIDATION.json',
        'docs/GAME-TELEMETRY-TOOL-PLAN.md',
        'docs/GAME-TOOL-CONNECTIONS.md',
        'docs/GAME-TOOLS-ARCHITECTURE.md',
        'docs/GAME-TOOLS-KNOWLEDGE-INDEX.md',
        'docs/GAME-TOOLS-MASTER-CHECKLIST.md',
        'docs/GAME_COVERAGE.md',
        'docs/GAP_AUDIT.md',
        'docs/GITHUB-PUBLISHING.md',
        'docs/INPUT-DEVICE-REGISTRY.md',
        'docs/INTEGRATION.md',
        'docs/KNOWLEDGE-MAINTENANCE.md',
        'docs/MERGER-DECISIONS-20261014.json',
        'docs/MOD-WORKFLOWS-INTEGRATION.md',
        'docs/MOD-WORKFLOWS.md',
        'docs/MODS-AI-BASELINE-MANIFEST.json',
        'docs/MODS-AI-INTEGRATION.md',
        'docs/MODS-AI-MODULE-BASELINE-MANIFEST.json',
        'docs/MODS-AI-SOURCE-DELTA.json',
        'docs/MODS-AI-START-HERE.html',
        'docs/MODS-AI-VALIDATION.json',
        'docs/OFFLINE-COMPARISON-REPORTS.md',
        'docs/OPERATING-STANDARD.md',
        'docs/OVERLAY-GROUPS.md',
        'docs/PUBLIC_SOURCES.json',
        'docs/RECIPES.md',
        'docs/RECOVERY.md',
        'docs/REVIEW_NOTES.md',
        'docs/TOOL-RESOURCE-OVERHEAD.md',
        'docs/UNIFIED-GAME-TOOLS.md',
        'docs/UNIFIED-TOOLKIT-CONTINUATION-2026-10-12.json',
        'docs/UNIFIED-TOOLKIT-CONTINUATION-2026-10-12.md',
        'docs/UNIFIED-UI-DESIGN.md',
        'docs/WORKBENCH-REVIEW.md',
        'docs/WORKBENCH-SOURCE-DELTA.json',
        'docs/WORKBENCH-VALIDATION.json',
        'docs/WORKSTREAM-AUDIT-2026-10-13.json',
        'examples/adapter-sdk/named_tokens.py',
        'examples/game-input/AzeronOverlayStudio.integrated.ahk',
        'examples/game-input/GameInputModule.ahk',
        'examples/game-input/HostIntegration.example.ahk',
        'examples/game-input/OTHER-CHAT-HANDOFF.txt',
        'examples/game-input/OVERLAY-STUDIO-INTEGRATION.md',
        'examples/game-input/OverlayStudioGameInput.ahk',
        'examples/game-input/PICTURE-BUTTONS.md',
        'examples/game-input/README.md',
        'examples/game-input/Start-GameInput.ahk',
        'examples/game-input/StudioHubBridge.ahk',
        'examples/game-input/StudioOverlayGroups.ahk',
        'examples/game-input/StudioPictureModule.ahk',
        'examples/game-input/VALIDATION.json',
        'examples/game-input/baseline/ControlHelper-v031.ahk',
        'examples/game-input/tests/Test-MicEditor.ahk',
        'examples/game-input/tests/Test-OverlayGroups.ahk',
        'examples/game-input/tests/Test-PictureEditor.ahk',
        'examples/game-input/tests/Test-PictureModule.ahk',
        'examples/game-input/tests/Test-UIFeedback.ahk',
        'examples/game-tool-hub/COMPARISON-DATASET.md',
        'examples/game-tool-hub/MOD-WORKFLOWS-CAPABILITIES.json',
        'examples/game-tool-hub/README.md',
        'examples/game-tool-hub/Start-GameToolHub.ps1',
        'examples/game-tool-hub/ai-plan-request.example.json',
        'examples/game-tool-hub/catalog.example.json',
        'examples/game-tool-hub/comparison-fixture.example.json',
        'examples/game-tool-hub/form-draft.example.json',
        'examples/game-tool-hub/game-support/cyberpunk-2077.json',
        'examples/game-tool-hub/game-support/pathfinder-kingmaker.json',
        'examples/game-tool-hub/game-support/pathfinder-wrath-of-the-righteous.json',
        'examples/game-tool-hub/game-support/skyrim-special-edition.json',
        'examples/game-tool-hub/game-support/stardew-valley.json',
        'examples/game-tool-hub/game-support/valheim.json',
        'examples/game-tool-hub/import-fixtures/cyberpunk-summary.example.json',
        'examples/game-tool-hub/import-fixtures/presentmon-no-animation-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-zero-stats.example.csv',
        'examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json',
        'examples/game-tool-hub/mod-recipes/stardew-valley.json',
        'examples/game-tool-hub/overlay-manifest.example.json',
        'examples/game-tool-hub/provider-health.example.json',
        'examples/game-tool-hub/scenario.example.json',
        'examples/game-tool-hub/workflow-diagnostic.example.json',
        'examples/game-tool-hub/workflow-installation.example.json',
        'examples/keybinds/game-locations.json',
        'examples/skyrim-special-edition/README.md',
        'examples/skyrim-special-edition/Skyrim-F12-Test.ahk',
        'game-packs/format-examples/sample-cfg-bind/fixtures/after.cfg',
        'game-packs/format-examples/sample-cfg-bind/fixtures/before.cfg',
        'game-packs/format-examples/sample-cfg-bind/pack.json',
        'game-packs/format-examples/sample-colon-lines/fixtures/after.txt',
        'game-packs/format-examples/sample-colon-lines/fixtures/before.txt',
        'game-packs/format-examples/sample-colon-lines/pack.json',
        'game-packs/format-examples/sample-ini-sparse/fixtures/after.ini',
        'game-packs/format-examples/sample-ini-sparse/fixtures/before.ini',
        'game-packs/format-examples/sample-ini-sparse/pack.json',
        'game-packs/format-examples/sample-ini/fixtures/after.ini',
        'game-packs/format-examples/sample-ini/fixtures/before.ini',
        'game-packs/format-examples/sample-ini/pack.json',
        'game-packs/format-examples/sample-json/fixtures/after.json',
        'game-packs/format-examples/sample-json/fixtures/before.json',
        'game-packs/format-examples/sample-json/pack.json',
        'game-packs/format-examples/sample-jsonc/fixtures/after.jsonc',
        'game-packs/format-examples/sample-jsonc/fixtures/before.jsonc',
        'game-packs/format-examples/sample-jsonc/pack.json',
        'game-packs/format-examples/sample-keyvalues/fixtures/after.vdf',
        'game-packs/format-examples/sample-keyvalues/fixtures/before.vdf',
        'game-packs/format-examples/sample-keyvalues/pack.json',
        'game-packs/format-examples/sample-ue-chord/fixtures/after.ini',
        'game-packs/format-examples/sample-ue-chord/fixtures/before.ini',
        'game-packs/format-examples/sample-ue-chord/pack.json',
        'game-packs/format-examples/sample-ue-ini/fixtures/after.ini',
        'game-packs/format-examples/sample-ue-ini/fixtures/before.ini',
        'game-packs/format-examples/sample-ue-ini/pack.json',
        'game-packs/format-examples/sample-xml/fixtures/after.xml',
        'game-packs/format-examples/sample-xml/fixtures/before.xml',
        'game-packs/format-examples/sample-xml/pack.json',
        'game-packs/research-drafts/bayonetta-pc/AUTHORING.md',
        'game-packs/research-drafts/bayonetta-pc/location-evidence.json',
        'game-packs/research-drafts/bayonetta-pc/pack.json',
        'game-packs/research-drafts/bioshock-2-remastered/AUTHORING.md',
        'game-packs/research-drafts/bioshock-2-remastered/location-evidence.json',
        'game-packs/research-drafts/bioshock-2-remastered/pack.json',
        'game-packs/research-drafts/bioshock-infinite/AUTHORING.md',
        'game-packs/research-drafts/bioshock-infinite/location-evidence.json',
        'game-packs/research-drafts/bioshock-infinite/pack.json',
        'game-packs/research-drafts/bioshock-remastered/AUTHORING.md',
        'game-packs/research-drafts/bioshock-remastered/location-evidence.json',
        'game-packs/research-drafts/bioshock-remastered/pack.json',
        'game-packs/research-drafts/control/AUTHORING.md',
        'game-packs/research-drafts/control/location-evidence.json',
        'game-packs/research-drafts/control/pack.json',
        'game-packs/research-drafts/cyberpunk-2077/AUTHORING.md',
        'game-packs/research-drafts/cyberpunk-2077/location-evidence.json',
        'game-packs/research-drafts/cyberpunk-2077/pack.json',
        'game-packs/research-drafts/devil-may-cry-5/AUTHORING.md',
        'game-packs/research-drafts/devil-may-cry-5/location-evidence.json',
        'game-packs/research-drafts/devil-may-cry-5/pack.json',
        'game-packs/research-drafts/doom-the-dark-ages/AUTHORING.md',
        'game-packs/research-drafts/doom-the-dark-ages/location-evidence.json',
        'game-packs/research-drafts/doom-the-dark-ages/pack.json',
        'game-packs/research-drafts/god-of-war-ragnarok/AUTHORING.md',
        'game-packs/research-drafts/god-of-war-ragnarok/location-evidence.json',
        'game-packs/research-drafts/god-of-war-ragnarok/pack.json',
        'game-packs/research-drafts/gta-v-enhanced/AUTHORING.md',
        'game-packs/research-drafts/gta-v-enhanced/location-evidence.json',
        'game-packs/research-drafts/gta-v-enhanced/pack.json',
        'game-packs/research-drafts/hogwarts-legacy/AUTHORING.md',
        'game-packs/research-drafts/hogwarts-legacy/location-evidence.json',
        'game-packs/research-drafts/hogwarts-legacy/pack.json',
        'game-packs/research-drafts/middle-earth-shadow-of-war/AUTHORING.md',
        'game-packs/research-drafts/middle-earth-shadow-of-war/location-evidence.json',
        'game-packs/research-drafts/middle-earth-shadow-of-war/pack.json',
        'game-packs/research-drafts/nier-automata/AUTHORING.md',
        'game-packs/research-drafts/nier-automata/location-evidence.json',
        'game-packs/research-drafts/nier-automata/pack.json',
        'game-packs/research-drafts/path-of-exile-2/AUTHORING.md',
        'game-packs/research-drafts/path-of-exile-2/location-evidence.json',
        'game-packs/research-drafts/path-of-exile-2/pack.json',
        'game-packs/research-drafts/pathfinder-kingmaker/AUTHORING.md',
        'game-packs/research-drafts/pathfinder-kingmaker/location-evidence.json',
        'game-packs/research-drafts/pathfinder-kingmaker/pack.json',
        'game-packs/research-drafts/red-dead-redemption-2/AUTHORING.md',
        'game-packs/research-drafts/red-dead-redemption-2/location-evidence.json',
        'game-packs/research-drafts/red-dead-redemption-2/pack.json',
        'game-packs/research-drafts/v-rising/AUTHORING.md',
        'game-packs/research-drafts/v-rising/location-evidence.json',
        'game-packs/research-drafts/v-rising/pack.json',
        'preferences/GENERAL.md',
        'schemas/game-pack.schema.json',
        'schemas/semantic-intent.schema.json',
        'scripts/Backup-UnifiedTools.ps1',
        'scripts/Build-MergedRelease.py',
        'scripts/Build-OverlayContract.py',
        'scripts/Create-UnifiedToolsLaunchers.py',
        'scripts/Create-UnifiedToolsShortcut.ps1',
        'scripts/Export-GameInput.ps1',
        'scripts/Export-GameTools.ps1',
        'scripts/Game-Keybinds.py',
        'scripts/Game-Mod-Ops.py',
        'scripts/Game-Mod-Panel.py',
        'scripts/Game-Support.py',
        'scripts/Game-Tool-Catalog.py',
        'scripts/Game-Tool-Hub.py',
        'scripts/GameFgInspector.py',
        'scripts/GameFgPreflight.py',
        'scripts/GameToolAI.py',
        'scripts/GameToolAppearance.py',
        'scripts/GameToolAutomation.py',
        'scripts/GameToolAutomationPanel.py',
        'scripts/GameToolAzeronLayer.py',
        'scripts/GameToolCatalogBridge.py',
        'scripts/GameToolCatalogPanel.py',
        'scripts/GameToolCompactUI.py',
        'scripts/GameToolComparison.py',
        'scripts/GameToolComparisonPanel.py',
        'scripts/GameToolCoordinator.py',
        'scripts/GameToolCrashEvidence.py',
        'scripts/GameToolEvidencePanel.py',
        'scripts/GameToolFocusLaunch.pyw',
        'scripts/GameToolFocusPanels.py',
        'scripts/GameToolFocusUI.py',
        'scripts/GameToolGameWorkspaces.py',
        'scripts/GameToolJournal.py',
        'scripts/GameToolKeybindAI.py',
        'scripts/GameToolKeybindIntegration.py',
        'scripts/GameToolKeybindWorkspaces.py',
        'scripts/GameToolMerged.py',
        'scripts/GameToolModIntegration.py',
        'scripts/GameToolModernUI.py',
        'scripts/GameToolOverlay.py',
        'scripts/GameToolOverlayPanel.py',
        'scripts/GameToolReadiness.py',
        'scripts/GameToolReadinessPanel.py',
        'scripts/GameToolReportImport.py',
        'scripts/GameToolSessionPanel.py',
        'scripts/GameToolUnified.py',
        'scripts/GameToolUnifiedPanel.py',
        'scripts/GameToolUserData.py',
        'scripts/GameToolUserDataPanel.py',
        'scripts/GameToolWorkbench.py',
        'scripts/GameToolWorkbenchLaunch.pyw',
        'scripts/GameToolWorkflow.py',
        'scripts/GameToolWorkflowPanel.py',
        'scripts/GameToolWorkspace.py',
        'scripts/Install-GameToolsRelease.ps1',
        'scripts/Install-UnifiedTools.py',
        'scripts/Start-UnifiedTools.pyw',
        'scripts/check_host.py',
        'scripts/game_keybind_ops/__init__.py',
        'scripts/game_keybind_ops/adapter_registry.py',
        'scripts/game_keybind_ops/authoring.py',
        'scripts/game_keybind_ops/core.py',
        'scripts/game_keybind_ops/deps.py',
        'scripts/game_keybind_ops/discovery.py',
        'scripts/game_keybind_ops/documents.py',
        'scripts/game_keybind_ops/effective.py',
        'scripts/game_keybind_ops/format_extensions.py',
        'scripts/game_keybind_ops/key_codec.py',
        'scripts/game_keybind_ops/known_folders_reference.py',
        'scripts/game_keybind_ops/pack_cli.py',
        'scripts/game_keybind_ops/pack_panel.py',
        'scripts/game_keybind_ops/pack_transport.py',
        'scripts/game_keybind_ops/packs.py',
        'scripts/game_keybind_ops/panel.py',
        'scripts/game_keybind_ops/planner.py',
        'scripts/game_keybind_ops/recovery.py',
        'scripts/game_keybind_ops/store_discovery.py',
        'scripts/game_mod_ops/__init__.py',
        'scripts/game_mod_ops/archive.py',
        'scripts/game_mod_ops/cli.py',
        'scripts/game_mod_ops/definitions.py',
        'scripts/game_mod_ops/handoff.py',
        'scripts/game_mod_ops/managers.py',
        'scripts/game_mod_ops/network.py',
        'scripts/game_mod_ops/panel.py',
        'scripts/game_mod_ops/recipes.py',
        'scripts/game_mod_ops/safety.py',
        'scripts/game_mod_ops/support.py',
        'scripts/game_mod_ops/umm.py',
        'scripts/game_mod_ops/workflow.py',
        'scripts/keybind_demo.py',
        'scripts/run_checks.py',
        'scripts/tests/Render-GameToolModernUI.py',
        'scripts/tests/Run-NativePictureDesktop.py',
        'scripts/tests/Test-GameModOps.py',
        'scripts/tests/Test-GameModPanel.py',
        'scripts/tests/Test-GameSourceExport.ps1',
        'scripts/tests/Test-GameSupport.py',
        'scripts/tests/Test-GameSupportPackaging.py',
        'scripts/tests/Test-GameSupportPanel.py',
        'scripts/tests/Test-GameToolAppearance.py',
        'scripts/tests/Test-GameToolAutomation.py',
        'scripts/tests/Test-GameToolAutomationPanel.py',
        'scripts/tests/Test-GameToolAzeronLayer.py',
        'scripts/tests/Test-GameToolCatalog.py',
        'scripts/tests/Test-GameToolCatalogBridge.py',
        'scripts/tests/Test-GameToolCompactUI.py',
        'scripts/tests/Test-GameToolComparison.py',
        'scripts/tests/Test-GameToolComparisonCLI.py',
        'scripts/tests/Test-GameToolComparisonPanel.py',
        'scripts/tests/Test-GameToolCoordinator.py',
        'scripts/tests/Test-GameToolCrashEvidence.py',
        'scripts/tests/Test-GameToolEvidenceCLI.py',
        'scripts/tests/Test-GameToolEvidencePanel.py',
        'scripts/tests/Test-GameToolFocus.py',
        'scripts/tests/Test-GameToolFocusHost.py',
        'scripts/tests/Test-GameToolFocusLauncher.py',
        'scripts/tests/Test-GameToolGameWorkspaces.py',
        'scripts/tests/Test-GameToolHub.py',
        'scripts/tests/Test-GameToolHubCatalog.py',
        'scripts/tests/Test-GameToolJournal.py',
        'scripts/tests/Test-GameToolMerged.py',
        'scripts/tests/Test-GameToolModernUI.py',
        'scripts/tests/Test-GameToolOverlay.py',
        'scripts/tests/Test-GameToolReadiness.py',
        'scripts/tests/Test-GameToolReadinessCLI.py',
        'scripts/tests/Test-GameToolReadinessPanel.py',
        'scripts/tests/Test-GameToolReportImport.py',
        'scripts/tests/Test-GameToolReportImportCLI.py',
        'scripts/tests/Test-GameToolReportImportPanel.py',
        'scripts/tests/Test-GameToolSessionCLI.py',
        'scripts/tests/Test-GameToolSessionPanel.py',
        'scripts/tests/Test-GameToolUnified.py',
        'scripts/tests/Test-GameToolUserData.py',
        'scripts/tests/Test-GameToolUserDataPanel.py',
        'scripts/tests/Test-GameToolWorkbench.py',
        'scripts/tests/Test-GameToolWorkbenchLauncher.py',
        'scripts/tests/Test-GameToolWorkflow.py',
        'scripts/tests/Test-GameToolWorkflowCLI.py',
        'scripts/tests/Test-GameToolWorkflowPanel.py',
        'scripts/tests/Test-GameToolWorkspace.py',
        'scripts/tests/Test-GameToolsInstaller.py',
        'scripts/tests/Test-ModernStartup.py',
        'scripts/tests/Test-NativePictureLayout.py',
        'scripts/tests/Test-PictureHost.py',
        'scripts/tests/Test-UnifiedToolsLaunchers.py',
        'scripts/tests/test_effective.py',
        'scripts/tests/test_extended.py',
        'scripts/tests/test_extensibility.py',
        'scripts/tests/test_game_fg_inspector.py',
        'scripts/tests/test_game_fg_preflight.py',
        'scripts/tests/test_host_integration.py',
        'scripts/tests/test_keybinds.py',
        'scripts/tests/test_pack_integration.py',
        'scripts/tests/test_pack_panel.py',
        'scripts/tests/test_panel.py',
        'templates/AUTOMATION-TASK.example.json',
        'templates/EXPERIMENT-LOG.md',
        'templates/GAME-HISTORY.md',
        'templates/GAME-KEYBINDS.example.json',
        'templates/GAME-SUPPORT-AUTHORING.json',
        'templates/GAME-SUPPORT.example.json',
        'templates/INPUT-DEVICE.example.json',
        'templates/KNOWLEDGE-RECORD.example.json',
        'templates/MOD-CATALOG.md',
        'templates/MOD-WORKFLOW.example.json',
        'templates/OPTION-MENU.md',
        'templates/PREFERENCE-PROFILE.md',
        'templates/PROFILE-MANIFEST.example.json',
        'validation/FORMAT_ROUNDTRIPS.json',
        'validation/HOST_DEPENDENCIES.json',
        'validation/PACK_COVERAGE.json',
        'validation/PLANNER_REUSE.json',
        'validation/PUBLICATION_STATUS.json',
        'validation/SOURCE_DELTA.json',
        'validation/SOURCE_PRESERVATION.json',
        'validation/STATIC_CHECKS.json',
        'validation/VALIDATION.json',
        'validation/final/VALIDATION.json',
        'validation/previous-0.1/DEMO_RESULT.json',
        'validation/previous-0.1/HOST_DEPENDENCIES.json',
        'validation/previous-0.1/PLANNER_REUSE.json',
        'validation/previous-0.1/PUBLICATION_STATUS.json',
        'validation/previous-0.1/SOURCE_PRESERVATION.json',
        'validation/previous-0.1/STATIC_CHECKS.json',
        'validation/previous-0.1/VALIDATION.json'
    )
    @($inputPaths + $mergedPaths | Select-Object -Unique)
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
    $taskAllowed = @('.md', '.txt', '.html', '.json', '.ps1', '.py', '.pyw', '.ahk', '.csv')
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
    $taskStudioEntries = @($Plan | Where-Object path -eq 'examples/game-input/AzeronOverlayStudio.integrated.ahk')
    if ($taskStudioEntries.Count) {
        if ($taskStudioEntries.Count -ne 1) { throw 'Ambiguous Studio version source.' }
        $taskStudioMatches = [regex]::Matches($taskStudioEntries[0].text, 'this\.Version\s*:=\s*"([0-9][A-Za-z0-9.+_-]{0,63})"')
        if ($taskStudioMatches.Count -ne 1) { throw 'Exactly one Studio Version is required.' }
        $taskVersions['overlay_studio'] = $taskStudioMatches[0].Groups[1].Value
    }
    if ($Bundle -eq 'GameTools') {
        foreach ($taskComponent in @(@{name='tool_hub';path='scripts/Game-Tool-Hub.py'}, @{name='tool_catalog';path='scripts/Game-Tool-Catalog.py'})) {
            $taskEntries = @($Plan | Where-Object path -eq $taskComponent.path)
            if ($taskEntries.Count -ne 1) { throw "Missing component version source: $($taskComponent.path)" }
            $taskMatches = [regex]::Matches($taskEntries[0].text, '(?m)^VERSION\s*=\s*"([0-9][A-Za-z0-9.+_-]{0,63})"\s*$')
            if ($taskMatches.Count -ne 1) { throw "Exactly one component VERSION is required: $($taskComponent.path)" }
            $taskVersions[$taskComponent.name] = $taskMatches[0].Groups[1].Value
        }
        foreach ($taskComponent in @(@{name='coordinator';path='scripts/GameToolCoordinator.py'},
            @{name='journal';path='scripts/GameToolJournal.py'}, @{name='session_panel';path='scripts/GameToolSessionPanel.py'},
            @{name='crash_evidence';path='scripts/GameToolCrashEvidence.py'}, @{name='evidence_panel';path='scripts/GameToolEvidencePanel.py'},
            @{name='workflow';path='scripts/GameToolWorkflow.py'}, @{name='workflow_panel';path='scripts/GameToolWorkflowPanel.py'},
            @{name='readiness';path='scripts/GameToolReadiness.py'}, @{name='readiness_panel';path='scripts/GameToolReadinessPanel.py'},
            @{name='overlay';path='scripts/GameToolOverlay.py'}, @{name='overlay_panel';path='scripts/GameToolOverlayPanel.py'},
            @{name='azeron_layer';path='scripts/GameToolAzeronLayer.py'},
            @{name='compact_ui';path='scripts/GameToolCompactUI.py'}, @{name='appearance';path='scripts/GameToolAppearance.py'},
            @{name='modern_ui';path='scripts/GameToolModernUI.py'},
            @{name='unified';path='scripts/GameToolUnified.py'}, @{name='unified_panel';path='scripts/GameToolUnifiedPanel.py'},
            @{name='workspace';path='scripts/GameToolWorkspace.py'}, @{name='user_data';path='scripts/GameToolUserData.py'},
            @{name='user_data_panel';path='scripts/GameToolUserDataPanel.py'},
            @{name='mod_operations';path='scripts/game_mod_ops/__init__.py'},
            @{name='mod_integration';path='scripts/GameToolModIntegration.py'},
            @{name='ai_boundary';path='scripts/GameToolAutomation.py'},
            @{name='ai_panel';path='scripts/GameToolAutomationPanel.py'},
            @{name='game_workspaces';path='scripts/GameToolGameWorkspaces.py'},
            @{name='workbench';path='scripts/GameToolWorkbench.py'},
            @{name='ai_stdio';path='scripts/GameToolAI.py'})) {
            $taskEntries = @($Plan | Where-Object path -eq $taskComponent.path)
            # Historical/synthetic plans may omit this later optional slice.
            if ($taskEntries.Count -eq 0) { continue }
            if ($taskEntries.Count -ne 1) { throw "Ambiguous component source: $($taskComponent.path)" }
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
        exclusions=@('game/mod/interpreter binaries and archives', 'installed settings and picture assets', 'native/onboard/remapper profiles and device identities', 'Hub private registry, imported reports, private session journals, saved-evidence packets and private workflow recipes/plans', 'saves, credentials, private paths and raw logs/video', 'unlisted sources and third-party SDK headers')
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
