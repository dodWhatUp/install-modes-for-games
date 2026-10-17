param([string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$labDirectory = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $OutputDirectory) { $OutputDirectory = [IO.Path]::GetFullPath((Join-Path $labDirectory '..')) }
$bundlePath = [IO.Path]::GetFullPath((Join-Path $OutputDirectory 'POE2-Weapon-and-Skill-Switch-Lab-v0.1.zip'))
if (Test-Path -LiteralPath $bundlePath) { throw 'Bundle already exists; preserve it before creating another version.' }
$files = Get-ChildItem -LiteralPath $labDirectory -File | Sort-Object Name
$manifest = [ordered]@{schema_version=1;version='0.1';scope='Offline prototype and prepared, unrun live-account plan';files=@()}
foreach ($entry in $files) {
    $manifest.files += [ordered]@{name=$entry.Name;size=$entry.Length;sha256=(Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$stream = [IO.File]::Open($bundlePath, [IO.FileMode]::CreateNew)
$archive = [IO.Compression.ZipArchive]::new($stream, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($entry in $files) {
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $entry.FullName, ('POE2-Switch-Lab-v0.1/' + $entry.Name), [IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
    $manifestEntry = $archive.CreateEntry('POE2-Switch-Lab-v0.1/MANIFEST-SHA256.json')
    $writer = [IO.StreamWriter]::new($manifestEntry.Open(), [Text.UTF8Encoding]::new($false))
    try { $writer.Write(($manifest | ConvertTo-Json -Depth 8)) } finally { $writer.Dispose() }
} finally { $archive.Dispose(); $stream.Dispose() }
$verified = [IO.Compression.ZipFile]::OpenRead($bundlePath)
try {
    foreach ($record in $manifest.files) {
        $zipEntry = $verified.GetEntry('POE2-Switch-Lab-v0.1/' + $record.name)
        $digest = [Security.Cryptography.SHA256]::Create()
        $entryStream = $zipEntry.Open()
        try { $hash = [BitConverter]::ToString($digest.ComputeHash($entryStream)).Replace('-','').ToLowerInvariant() }
        finally { $entryStream.Dispose(); $digest.Dispose() }
        if ($hash -ne $record.sha256 -or $zipEntry.Length -ne $record.size) { throw ('Archive verification failed: ' + $record.name) }
    }
} finally { $verified.Dispose() }
[ordered]@{name=[IO.Path]::GetFileName($bundlePath);size=(Get-Item -LiteralPath $bundlePath).Length;sha256=(Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash;verified_payloads=$manifest.files.Count} | ConvertTo-Json
