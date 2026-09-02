[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string]$ManifestPath,

    [Parameter()]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Container })]
    [string]$GameRoot
)

$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()

if ($manifest.schemaVersion -ne 1) { $errors.Add('schemaVersion must be 1.') }
if ([string]::IsNullOrWhiteSpace($manifest.game)) { $errors.Add('game is required.') }
if ([string]::IsNullOrWhiteSpace($manifest.profile)) { $errors.Add('profile is required.') }
if (-not $manifest.featureOwnership) { $errors.Add('featureOwnership is required.') }

$allowedActions = @('add', 'replace')
$destinations = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$rootFull = if ($GameRoot) { [System.IO.Path]::GetFullPath($GameRoot).TrimEnd('\') } else { $null }
$results = [System.Collections.Generic.List[object]]::new()

foreach ($entry in @($manifest.files)) {
    $destination = [string]$entry.destination
    if ([string]::IsNullOrWhiteSpace($destination)) {
        $errors.Add('Every file entry requires destination.')
        continue
    }
    if ([System.IO.Path]::IsPathRooted($destination) -or $destination -match '(^|[\\/])\.\.([\\/]|$)') {
        $errors.Add("Unsafe destination: $destination")
        continue
    }
    if (-not $destinations.Add($destination)) { $errors.Add("Duplicate destination: $destination") }
    if ($allowedActions -notcontains [string]$entry.action) { $errors.Add("Invalid action for ${destination}: $($entry.action)") }
    if ($entry.sha256 -and [string]$entry.sha256 -notmatch '^[A-Fa-f0-9]{64}$') { $errors.Add("Invalid SHA-256 for ${destination}.") }

    if ($rootFull) {
        $target = [System.IO.Path]::GetFullPath((Join-Path $rootFull $destination))
        if (-not $target.StartsWith($rootFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            $errors.Add("Destination escapes game root: $destination")
            continue
        }
        $exists = Test-Path -LiteralPath $target -PathType Leaf
        $actualHash = if ($exists) { (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash } else { $null }
        $results.Add([pscustomobject]@{
            Destination = $destination
            Action = $entry.action
            Exists = $exists
            ActualSHA256 = $actualHash
            MatchesManifest = [bool]($entry.sha256 -and $actualHash -eq [string]$entry.sha256)
        })
    }
}

foreach ($processName in @($manifest.requiredStoppedProcesses)) {
    if (Get-Process -Name $processName -ErrorAction SilentlyContinue) {
        $errors.Add("Required stopped process is running: $processName")
    }
}

if ($errors.Count) {
    $errors | ForEach-Object { Write-Error $_ }
    throw "Profile manifest validation failed with $($errors.Count) error(s)."
}

[pscustomobject]@{
    Manifest = (Resolve-Path -LiteralPath $ManifestPath).Path
    Game = $manifest.game
    Profile = $manifest.profile
    FileEntries = @($manifest.files).Count
    ConfigurationEntries = @($manifest.configuration).Count
    Valid = $true
}

if ($rootFull) { $results }
