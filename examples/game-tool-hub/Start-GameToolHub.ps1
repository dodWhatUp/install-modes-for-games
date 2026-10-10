[CmdletBinding()]
param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$hubSource = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../scripts/Game-Tool-Hub.py'))
if (-not (Test-Path -LiteralPath $hubSource -PathType Leaf)) { throw 'Game Tool Hub source is missing.' }
if (-not $PythonPath) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/pythonw.exe'
    if (Test-Path -LiteralPath $bundledPython -PathType Leaf) { $PythonPath = $bundledPython }
    else {
        $pythonCommand = Get-Command pythonw.exe -ErrorAction SilentlyContinue
        if ($pythonCommand) { $PythonPath = $pythonCommand.Source }
    }
}
if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw 'Python with Tk is required. Pass -PythonPath with the installed pythonw.exe path.'
}
Start-Process -FilePath $PythonPath -ArgumentList ('"' + $hubSource + '"') -WindowStyle Normal
