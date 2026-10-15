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
    param(
        [ValidateSet('GameTools', 'GameInput')][string]$Bundle,
        [string]$RepositoryRoot = ''
    )
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
    $taskPaths = $inputPaths + @(
        'AGENTS.md',
        'preferences/GENERAL.md',
        'docs/GAME-TOOLS-KNOWLEDGE-INDEX.md',
        'docs/UI-AND-CONTENT-DESIGN.md',
        'docs/UNIFIED-TOOLKIT-CONTINUATION-2026-10-12.md',
        'docs/UNIFIED-TOOLKIT-CONTINUATION-2026-10-12.json',
        'docs/GAME-TOOLS-MASTER-CHECKLIST.md',
        'docs/GAME-TELEMETRY-TOOL-PLAN.md',
        'docs/OFFLINE-COMPARISON-REPORTS.md',
        'docs/KNOWLEDGE-MAINTENANCE.md',
        'docs/AUTOMATION-OPERATING-PROCEDURES.md',
        'docs/TOOL-RESOURCE-OVERHEAD.md',
        'docs/GAME-PERFORMANCE-MEASUREMENT.md',
        'docs/GAME-TOOL-CONNECTIONS.md',
        'docs/OPERATING-STANDARD.md',
        'docs/FEATURE-DECISION.md',
        'docs/AZERON-GAME-CONTROLS.md',
        'docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md',
        'docs/INPUT-DEVICE-REGISTRY.md',
        'docs/GITHUB-PUBLISHING.md',
        'docs/DISTRIBUTION.md',
        'examples/game-tool-hub/README.md',
        'examples/game-tool-hub/Start-GameToolHub.ps1',
        'examples/game-tool-hub/form-draft.example.json',
        'examples/game-tool-hub/catalog.example.json',
        'examples/game-tool-hub/comparison-fixture.example.json',
        'examples/game-tool-hub/COMPARISON-DATASET.md',
        'scripts/Game-Tool-Hub.py',
        'scripts/GameToolCatalogBridge.py',
        'scripts/GameToolCatalogPanel.py',
        'scripts/GameToolComparison.py',
        'scripts/GameToolComparisonPanel.py',
        'scripts/GameToolReportImport.py',
        'scripts/GameToolJournal.py',
        'scripts/GameToolCoordinator.py',
        'scripts/GameToolSessionPanel.py',
        'scripts/GameToolCrashEvidence.py',
        'scripts/GameToolEvidencePanel.py',
        'scripts/GameToolWorkflow.py',
        'scripts/GameToolWorkflowPanel.py',
        'scripts/GameToolReadiness.py',
        'scripts/GameToolReadinessPanel.py',
        'scripts/GameToolOverlay.py',
        'scripts/GameToolOverlayPanel.py',
        'scripts/GameToolAzeronLayer.py',
        'scripts/tests/Test-GameToolAzeronLayer.py',
        'scripts/GameToolCompactUI.py',
        'scripts/GameToolAppearance.py',
        'scripts/GameToolGameWorkspaces.py',
        'scripts/GameToolWorkbench.py',
        'scripts/GameToolWorkbenchLaunch.pyw',
        'scripts/tests/Test-GameToolGameWorkspaces.py',
        'scripts/tests/Test-GameToolWorkbench.py',
        'scripts/tests/Test-GameToolWorkbenchLauncher.py',
        'docs/WORKBENCH-REVIEW.md',
        'docs/WORKBENCH-VALIDATION.json',
        'docs/WORKBENCH-SOURCE-DELTA.json',
        'scripts/GameToolFocusUI.py',
        'scripts/GameToolFocusPanels.py',
        'scripts/GameToolFocusLaunch.pyw',
        'scripts/tests/Test-GameToolFocus.py',
        'scripts/tests/Test-GameToolFocusHost.py',
        'scripts/tests/Test-GameToolFocusLauncher.py',
        'docs/FOCUS-UI-REVIEW.md',
        'docs/WORKSTREAM-AUDIT-2026-10-13.json',
        'docs/FOCUS-UI-PRIOR-ARTIFACTS.json',
        'docs/FOCUS-UI-VALIDATION.json',
        'docs/FOCUS-UI-SOURCE-DELTA.json',
        'scripts/GameToolModernUI.py',
        'scripts/tests/Test-GameToolModernUI.py',
        'scripts/tests/Render-GameToolModernUI.py',
        'scripts/tests/Test-GameToolAppearance.py',
        'docs/UNIFIED-UI-DESIGN.md',
        'scripts/tests/Test-GameToolCompactUI.py',
        'scripts/Build-OverlayContract.py',
        'scripts/Install-GameToolsRelease.ps1',
        'scripts/GameToolUnified.py',
        'scripts/GameToolUnifiedPanel.py',
        'scripts/GameToolWorkspace.py',
        'scripts/GameToolUserData.py',
        'scripts/GameToolUserDataPanel.py',
        'scripts/tests/Test-GameToolWorkspace.py',
        'scripts/tests/Test-GameToolUserData.py',
        'scripts/tests/Test-GameToolUserDataPanel.py',
        'scripts/Start-UnifiedTools.pyw',
        'scripts/Install-UnifiedTools.py',
        'scripts/Create-UnifiedToolsLaunchers.py',
        'scripts/Create-UnifiedToolsShortcut.ps1',
        'scripts/tests/Test-UnifiedToolsLaunchers.py',
        'scripts/Backup-UnifiedTools.ps1',
        'scripts/tests/Test-GameToolUnified.py',
        'docs/UNIFIED-GAME-TOOLS.md',
        'scripts/tests/Test-GameToolOverlay.py',
        'scripts/tests/Test-GameToolsInstaller.py',
        'docs/OVERLAY-GROUPS.md',
        'examples/game-tool-hub/overlay-manifest.example.json',
        'scripts/tests/Test-GameToolReadiness.py',
        'scripts/tests/Test-GameToolReadinessPanel.py',
        'scripts/tests/Test-GameToolReadinessCLI.py',
        'examples/game-tool-hub/provider-health.example.json',
        'examples/game-tool-hub/scenario.example.json',
        'scripts/tests/Test-GameToolWorkflow.py',
        'scripts/tests/Test-GameToolWorkflowPanel.py',
        'scripts/tests/Test-GameToolWorkflowCLI.py',
        'examples/game-tool-hub/workflow-installation.example.json',
        'examples/game-tool-hub/workflow-diagnostic.example.json',
        'scripts/tests/Test-GameToolCrashEvidence.py',
        'scripts/tests/Test-GameToolEvidencePanel.py',
        'scripts/tests/Test-GameToolEvidenceCLI.py',
        'scripts/tests/Test-GameToolJournal.py',
        'scripts/tests/Test-GameToolCoordinator.py',
        'scripts/tests/Test-GameToolSessionPanel.py',
        'scripts/tests/Test-GameToolSessionCLI.py',
        'scripts/GameFgInspector.py',
        'scripts/GameFgPreflight.py',
        'scripts/Game-Tool-Catalog.py',
        'scripts/tests/Test-GameToolHub.py',
        'scripts/tests/Test-GameToolCatalogBridge.py',
        'scripts/tests/Test-GameToolHubCatalog.py',
        'scripts/tests/Test-GameToolComparison.py',
        'scripts/tests/Test-GameToolComparisonPanel.py',
        'scripts/tests/Test-GameToolComparisonCLI.py',
        'scripts/tests/Test-GameToolReportImport.py',
        'scripts/tests/Test-GameToolReportImportPanel.py',
        'scripts/tests/Test-GameToolReportImportCLI.py',
        'examples/game-tool-hub/import-fixtures/cyberpunk-summary.example.json',
        'examples/game-tool-hub/import-fixtures/presentmon-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-no-animation-stats.example.csv',
        'examples/game-tool-hub/import-fixtures/presentmon-zero-stats.example.csv',
        'scripts/tests/test_game_fg_inspector.py',
        'scripts/tests/test_game_fg_preflight.py',
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
        'templates/PREFERENCE-PROFILE.md',
        'docs/MOD-WORKFLOWS-INTEGRATION.md',
        'docs/MOD-WORKFLOWS.md',
        'docs/MODS-AI-BASELINE-MANIFEST.json',
        'docs/MODS-AI-INTEGRATION.md',
        'docs/MODS-AI-MODULE-BASELINE-MANIFEST.json',
        'docs/MODS-AI-SOURCE-DELTA.json',
        'docs/MODS-AI-START-HERE.html',
        'docs/MODS-AI-VALIDATION.json',
        'examples/game-tool-hub/MOD-WORKFLOWS-CAPABILITIES.json',
        'examples/game-tool-hub/ai-plan-request.example.json',
        'examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json',
        'scripts/Game-Mod-Ops.py',
        'scripts/Game-Mod-Panel.py',
        'scripts/GameToolAI.py',
        'scripts/GameToolAIContracts.py',
        'scripts/GameToolAITools.py',
        'scripts/GameToolAIKnowledge.py',
        'scripts/GameToolAIFoundation.py',
        'scripts/GameToolAIModern.py',
        'scripts/tests/Test-GameToolAIFoundation.py',
        'scripts/tests/Test-GameToolAIModern.py',
        'scripts/tests/GameToolAITestPackage.py',
        'scripts/tests/requirements.txt',
        'docs/AI-EFFICIENCY-FOUNDATION.md',
        'docs/AI-EFFICIENCY-FOUNDATION-REVIEW.md',
        'docs/AI-EFFICIENCY-FOUNDATION-VALIDATION.json',
        'docs/AI-EFFICIENCY-FOUNDATION-SOURCE-DELTA.json',
        'docs/AI-EFFICIENCY-FOUNDATION-LIMITATIONS.md',
        'docs/AI-EFFICIENCY-FOUNDATION-CONTINUATION.md',
        'docs/AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md',
        'docs/AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json',
        'docs/AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.md',
        'docs/AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.json',
        'docs/AI-PLANNING-READONLY-SLICE.md',
        'docs/AI-PLANNING-READONLY-VALIDATION.json',
        'docs/MO2-READ-ADAPTER.md',
        'docs/MO2-READ-ADAPTER-VALIDATION.json',
        'docs/MO2-READ-ADAPTER-SOURCE-DELTA.json',
        'schemas/ai-result-envelope.schema.json',
        'schemas/game-tools-goal-plan.schema.json',
        'schemas/mo2-profile-state.schema.json',
        'scripts/GameToolInstances.py',
        'scripts/GameToolPlanning.py',
        'scripts/GameToolMO2Read.py',
        'scripts/Game-Instances.py',
        'scripts/tests/Test-GameToolPlanning.py',
        'scripts/tests/Test-GameToolMO2Read.py',
        'scripts/GameToolAutomation.py',
        'scripts/GameToolAutomationPanel.py',
        'scripts/GameToolModIntegration.py',
        'scripts/game_mod_ops/__init__.py',
        'scripts/game_mod_ops/archive.py',
        'scripts/game_mod_ops/cli.py',
        'scripts/game_mod_ops/network.py',
        'scripts/game_mod_ops/panel.py',
        'scripts/game_mod_ops/recipes.py',
        'scripts/game_mod_ops/safety.py',
        'scripts/game_mod_ops/umm.py',
        'scripts/game_mod_ops/workflow.py',
        'scripts/tests/Test-GameModOps.py',
        'scripts/tests/Test-GameModPanel.py',
        'scripts/tests/Test-GameToolAutomation.py',
        'scripts/tests/Test-GameToolAutomationPanel.py',
        'templates/MOD-WORKFLOW.example.json',
        'scripts/game_mod_ops/definitions.py',
        'scripts/game_mod_ops/managers.py',
        'scripts/game_mod_ops/support.py',
        'scripts/game_mod_ops/handoff.py',
        'scripts/Game-Support.py',
        'scripts/tests/Test-GameSupport.py',
        'scripts/tests/Test-GameSupportPanel.py',
        'scripts/tests/Test-GameSupportPackaging.py',
        'docs/GAME-SUPPORT-PACKS.md',
        'docs/GAME-SUPPORT-VALIDATION.json',
        'docs/GAME-SUPPORT-SOURCE-DELTA.json',
        'templates/GAME-SUPPORT.example.json',
        'templates/GAME-SUPPORT-AUTHORING.json',
        'examples/game-tool-hub/mod-recipes/stardew-valley.json',
        'examples/game-tool-hub/game-support/cyberpunk-2077.json',
        'examples/game-tool-hub/game-support/pathfinder-kingmaker.json',
        'examples/game-tool-hub/game-support/pathfinder-wrath-of-the-righteous.json',
        'examples/game-tool-hub/game-support/skyrim-special-edition.json',
        'examples/game-tool-hub/game-support/stardew-valley.json',
        'examples/game-tool-hub/game-support/valheim.json',
        'docs/KEYBINDS-MERGE-CONTINUATION.md',
        'docs/KEYBINDS-MERGE-INTAKE.json',
        'docs/KEYBINDS-MERGE-LIMITATIONS.md',
        'docs/KEYBINDS-MERGE-REVIEW.md',
        'docs/KEYBINDS-MERGE-SOURCE-DELTA.json',
        'docs/KEYBINDS-MERGE-VALIDATION.json',
        'docs/keybinds/COMPONENT-CHECKPOINT.md',
        'docs/keybinds/README.md',
        'docs/keybinds/history/INTEGRATION-HANDOFF-B-0.2.0-preview.1.md',
        'docs/keybinds/history/DEPENDENCY_PINS-B-0.2.0-preview.1.json',
        'docs/keybinds/COMPONENT-README.md',
        'docs/keybinds/DEPENDENCY_PINS.json',
        'docs/keybinds/EXTENSION_GUIDE.md',
        'docs/keybinds/GAME_COVERAGE.md',
        'docs/keybinds/GAP_AUDIT.md',
        'docs/keybinds/INPUT-B-MANIFEST.json',
        'docs/keybinds/INTEGRATION-HANDOFF.md',
        'docs/keybinds/INTEGRATION.md',
        'docs/keybinds/ORIGINAL-OPENING-MESSAGE-HE.txt',
        'docs/keybinds/PUBLIC_SOURCES.json',
        'docs/keybinds/RECIPES.md',
        'docs/keybinds/RECOVERY.md',
        'docs/keybinds/REVIEW_NOTES.md',
        'examples/adapter-sdk/named_tokens.py',
        'examples/keybinds/game-locations.json',
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
        'schemas/game-pack.schema.json',
        'schemas/semantic-intent.schema.json',
        'scripts/Game-Keybinds.py',
        'scripts/GameToolKeybindAI.py',
        'scripts/GameToolKeybindIntegration.py',
        'scripts/GameToolKeybindWorkspaces.py',
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
        'scripts/keybind_demo.py',
        'scripts/tests/Run-KeybindChecks.py',
        'scripts/tests/Test-GameToolKeybindMerge.py',
        'scripts/tests/keybinds/test_effective.py',
        'scripts/tests/keybinds/test_extended.py',
        'scripts/tests/keybinds/test_extensibility.py',
        'scripts/tests/keybinds/test_host_integration.py',
        'scripts/tests/keybinds/test_keybinds.py',
        'scripts/tests/keybinds/test_pack_integration.py',
        'scripts/tests/keybinds/test_schema_contract.py',
        'scripts/tests/keybinds/test_pack_panel.py',
        'scripts/tests/keybinds/test_panel.py'
    )
    if (!$RepositoryRoot) { $RepositoryRoot = Split-Path -Parent $PSScriptRoot }
    foreach ($taskOptional in @(
        'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md',
        'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json'
    )) {
        if (Test-Path -LiteralPath (Join-Path $RepositoryRoot $taskOptional) -PathType Leaf) {
            $taskPaths += $taskOptional
        }
    }
    return $taskPaths
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
            (Get-GameSourceHash -Bytes ([IO.File]::ReadAllBytes($taskSource))) -ne $taskEntry.sha256) {
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
    $taskAllowed = @('.md', '.txt', '.html', '.json', '.jsonc', '.ps1', '.py', '.pyw', '.ahk', '.csv', '.ini', '.cfg', '.vdf', '.xml')
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
            @{name='mod_ops';path='scripts/game_mod_ops/__init__.py'},
            @{name='mod_integration';path='scripts/GameToolModIntegration.py'},
            @{name='automation';path='scripts/GameToolAutomation.py'},
            @{name='automation_panel';path='scripts/GameToolAutomationPanel.py'},
            @{name='game_workspaces';path='scripts/GameToolGameWorkspaces.py'},
            @{name='workbench';path='scripts/GameToolWorkbench.py'},
            @{name='ai_transport';path='scripts/GameToolAI.py'},
            @{name='instances';path='scripts/GameToolInstances.py'},
            @{name='planning';path='scripts/GameToolPlanning.py'},
            @{name='mo2_read';path='scripts/GameToolMO2Read.py'},
            @{name='keybinds';path='scripts/GameToolKeybindIntegration.py'})) {
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
        else { "Unified-Game-Tools-$($taskVersions.tool_hub)-Keybinds-Reviewed-Source-$ClientDate.zip" }
    $taskMo2AcceptanceMd = if (@($Plan | Where-Object path -eq 'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md').Count) { 'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md' } else { $null }
    $taskMo2AcceptanceJson = if (@($Plan | Where-Object path -eq 'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json').Count) { 'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json' } else { $null }
    $taskMo2RuntimeStatus = if ($taskMo2AcceptanceMd -and $taskMo2AcceptanceJson) {
        'A separate bounded MO2 Windows/source-package/external-client acceptance record is included. Export itself performs no runtime or real-game acceptance; real-profile, installation and main adoption remain separate.'
    } else {
        'MO2 Windows, complete dependency-backed suites, source-package and external-client acceptance remain pending. Export itself performs no runtime or real-game acceptance.'
    }
    return [ordered]@{
        schema_version=1; bundle=$Bundle; bundle_kind='authored-source-and-sanitized-knowledge-checkpoint'
        client_date=$ClientDate; client_timezone='Asia/Jerusalem'; component_versions=$taskVersions
        archive_name=$taskArchiveName; source='https://github.com/dodWhatUp/install-modes-for-games'
        source_state='MO2 read-only adapter 0.28 task-branch source based on adopted canonical main 290bea7983ccca50073c5f45ce44337cacafc32a; exact source bytes and sanitized evidence; not claimed merged into main.'
        canonical_reference_revision='290bea7983ccca50073c5f45ce44337cacafc32a'
        canonical_reference_meaning='Exact adopted-main base after the 0.27 read-only planning source and its adoption record. This later 0.28 task branch is not main adoption.'
        windows_acceptance_reference='docs/AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json'
        reconciliation_reference='docs/AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.json'
        planning_contract_reference='docs/AI-PLANNING-READONLY-SLICE.md'
        mo2_contract_reference=if (@($Plan | Where-Object path -eq 'docs/MO2-READ-ADAPTER.md').Count) { 'docs/MO2-READ-ADAPTER.md' } else { $null }
        mo2_validation_reference=if (@($Plan | Where-Object path -eq 'docs/MO2-READ-ADAPTER-VALIDATION.json').Count) { 'docs/MO2-READ-ADAPTER-VALIDATION.json' } else { $null }
        mo2_source_delta_reference=if (@($Plan | Where-Object path -eq 'docs/MO2-READ-ADAPTER-SOURCE-DELTA.json').Count) { 'docs/MO2-READ-ADAPTER-SOURCE-DELTA.json' } else { $null }
        mo2_windows_acceptance_reference=$taskMo2AcceptanceMd
        mo2_windows_acceptance_json_reference=$taskMo2AcceptanceJson
        runtime_status=$taskMo2RuntimeStatus
        input_validation_reference='examples/game-input/VALIDATION.json'; input_recorded_date=$taskValidation.recorded_date
        input_declared_runtime=$taskValidation.preview_runtime
        exclusions=@('game/mod/interpreter binaries and archives', 'installed settings and picture assets', 'native/onboard/remapper profiles and device identities', 'Hub private registry, imported reports, private session journals, saved-evidence packets and private workflow recipes/plans', 'saves, credentials, private paths and raw logs/video', 'unlisted sources and third-party SDK headers')
        recovery_boundary='Source restoration only, not full installed-tool/game/native-profile recovery. Private backups and supported runtimes are separate requirements. Restore/import acceptance is not established by archive integrity.'
        integration_validation_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-VALIDATION.json').Count) { 'docs/KEYBINDS-MERGE-VALIDATION.json' } else { $null }
        source_delta_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-SOURCE-DELTA.json').Count) { 'docs/KEYBINDS-MERGE-SOURCE-DELTA.json' } else { $null }
        merge_review_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-REVIEW.md').Count) { 'docs/KEYBINDS-MERGE-REVIEW.md' } else { $null }
        merge_intake_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-INTAKE.json').Count) { 'docs/KEYBINDS-MERGE-INTAKE.json' } else { $null }
        limitations_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-LIMITATIONS.md').Count) { 'docs/KEYBINDS-MERGE-LIMITATIONS.md' } else { $null }
        continuation_reference=if (@($Plan | Where-Object path -eq 'docs/KEYBINDS-MERGE-CONTINUATION.md').Count) { 'docs/KEYBINDS-MERGE-CONTINUATION.md' } else { $null }
    }
}

function Get-GameUnbundledReferences {
    param([string]$RepositoryRoot, [object[]]$Plan, [string]$CanonicalRevision)
    if ($CanonicalRevision -notmatch '^[a-f0-9]{40}$') { throw 'An exact canonical reference revision is required.' }
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
                    canonical_revision=$CanonicalRevision
                    canonical_source='https://github.com/dodWhatUp/install-modes-for-games/blob/' + $CanonicalRevision + '/' + (($taskRelative -split '/' | ForEach-Object { [Uri]::EscapeDataString($_) }) -join '/')
                    exists_in_checkout=(Test-Path -LiteralPath $taskResolved); note='Not bundled; exact reference pin does not prove publication, access or runtime acceptance.' }
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
    $taskManifest.unbundled_references = @(Get-GameUnbundledReferences -RepositoryRoot $taskRoot -Plan $Plan -CanonicalRevision ([string]$Metadata.canonical_reference_revision))
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
        sha256=(Get-GameSourceHash -Bytes ([IO.File]::ReadAllBytes($taskZip)));manifest_sha256=(Get-GameSourceHash -Bytes $taskManifestBytes)
        integrity='all_source_and_manifest_zip_entries_verified';source_current_at_final_hash_check=$true;source_checked_utc=[DateTime]::UtcNow.ToString('o')
        recovery='source_checkpoint_not_full_recovery'}
}

if (!$LibraryOnly) {
    $taskRepository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    if ($ClientDate -eq '') { $ClientDate = Get-GameExportClientDate }
    $taskPlan = Get-GameSourcePlan -RepositoryRoot $taskRepository -RelativePaths (Get-GameSourcePaths -Bundle $Bundle -RepositoryRoot $taskRepository)
    $taskMetadata = Get-GameBundleMetadata -Bundle $Bundle -Plan $taskPlan -ClientDate $ClientDate
    Invoke-GameSourceExport -RepositoryRoot $taskRepository -OutputDirectory $OutputDirectory -Plan $taskPlan -Metadata $taskMetadata |
        ConvertTo-Json -Depth 8
}
