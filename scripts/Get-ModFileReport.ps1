[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $GameDirectory,

    [string] $OutputPath = (Join-Path $PWD 'mod-file-report.csv'),

    [switch] $Recurse
)

$ErrorActionPreference = 'Stop'

$resolvedGame = (Resolve-Path -LiteralPath $GameDirectory).Path
if (-not (Test-Path -LiteralPath $resolvedGame -PathType Container)) {
    throw "Game directory does not exist: $resolvedGame"
}

$resolvedOutput = [IO.Path]::GetFullPath($OutputPath)
$extensions = @('.addon', '.addon32', '.addon64', '.asi', '.cfg', '.dll',
                '.exe', '.ini', '.json', '.log', '.toml')

$search = @{
    LiteralPath = $resolvedGame
    File        = $true
    Force       = $true
}
if ($Recurse) {
    $search.Recurse = $true
}

$rows = foreach ($file in Get-ChildItem @search) {
    if ($extensions -notcontains $file.Extension.ToLowerInvariant()) {
        continue
    }

    $relative = [IO.Path]::GetRelativePath($resolvedGame, $file.FullName)
    $version = $file.VersionInfo
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash

    [pscustomobject]@{
        RelativePath      = $relative
        Length            = $file.Length
        LastWriteTimeUtc  = $file.LastWriteTimeUtc.ToString('o')
        FileVersion       = $version.FileVersion
        ProductVersion    = $version.ProductVersion
        CompanyName       = $version.CompanyName
        SHA256            = $hash
    }
}

$rows |
    Sort-Object RelativePath |
    Export-Csv -LiteralPath $resolvedOutput -NoTypeInformation -Encoding utf8

Write-Host "Wrote $($rows.Count) file records to $resolvedOutput"
