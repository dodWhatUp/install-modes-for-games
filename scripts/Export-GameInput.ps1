param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$ClientDate = ''
)
$ErrorActionPreference = 'Stop'
$taskRequestedOutput = $OutputDirectory
$taskRequestedDate = $ClientDate

# Shared source-export library; no app/input route or archive is started by import.
. (Join-Path $PSScriptRoot 'Export-GameTools.ps1') -LibraryOnly
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ($taskRequestedDate -eq '') { $taskRequestedDate = Get-GameExportClientDate }
$taskPlan = Get-GameSourcePlan -RepositoryRoot $taskRepo -RelativePaths (Get-GameSourcePaths -Bundle GameInput)
$taskMetadata = Get-GameBundleMetadata -Bundle GameInput -Plan $taskPlan -ClientDate $taskRequestedDate
Invoke-GameSourceExport -RepositoryRoot $taskRepo -OutputDirectory $taskRequestedOutput -Plan $taskPlan -Metadata $taskMetadata |
    ConvertTo-Json -Depth 8
