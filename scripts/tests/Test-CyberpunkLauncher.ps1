#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory)][string]$WrapperPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$base = Join-Path ([IO.Path]::GetTempPath()) ('cyberpunk-launcher-test-' + [guid]::NewGuid().ToString('N'))
$checks = 0
function Assert($Value, [string]$Message) {
    if (-not $Value) { throw "ASSERTION FAILED: $Message" }
    $script:checks++
}
function Json([string]$Path, $Object) { [IO.File]::WriteAllText($Path, ($Object | ConvertTo-Json -Depth 20)) }
function Make-Package([string]$Id, [string]$Target, $Dependencies = @()) {
    $path = Join-Path $base ('staging/' + $Id)
    $null = New-Item -ItemType Directory -Path $path -Force
    [IO.File]::WriteAllText((Join-Path $path 'file.txt'), $Id)
    Json (Join-Path $path 'component.json') @{ schemaVersion = 1; id = $Id; version = 'fixture'; source = 'https://example.invalid/fixture'; dependencies = @($Dependencies);
        files = @(@{root='game';path=$Target;payload='file.txt'}) }
}
foreach ($dir in @('game/bin/x64','user','tools','staging')) { $null = New-Item -ItemType Directory -Path (Join-Path $base $dir) -Force }
$wrapper = Join-Path $base 'Manage-Cyberpunk.ps1'
Copy-Item -LiteralPath $WrapperPath -Destination $wrapper
$production = Join-Path (Split-Path -Parent $PSScriptRoot) 'Manage-ModComponents.ps1'
$source = Get-Content -LiteralPath $production -Raw
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
$guard = $ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-Stopped'}, $false)
$source = $source.Substring(0,$guard.Extent.StartOffset) + 'function Assert-Stopped($Extra = @()) {}' + $source.Substring($guard.Extent.EndOffset)
[IO.File]::WriteAllText((Join-Path $base 'tools/Manage-ModComponents.ps1'), $source)
$game = Join-Path $base 'game'
$user = Join-Path $base 'user'
Json (Join-Path $base 'roots.json') @{ game=$game; user=$user }
Json (Join-Path $base 'configuration-snapshot.json') @(@{root='user';path='UserSettings.json'},@{root='game';path='bin/x64/OptiScaler.ini'})
[IO.File]::WriteAllText((Join-Path $user 'UserSettings.json'), 'personal-settings')
[IO.File]::WriteAllText((Join-Path $game 'bin/x64/OptiScaler.ini'), '[Plugins]LoadReshade=true')
Make-Package 'reshade-6.8.0' 'bin/x64/ReShade64.dll'
Make-Package 'independent-qol' 'qol.txt'
& $wrapper -Command ImportStaged | Out-Null
Assert (-not (Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll'))) 'Wrapper import does not deploy'
$managed = Get-Content -LiteralPath (Join-Path $base 'component-state/state.json') -Raw | ConvertFrom-Json
Assert (@($managed.components).Count -eq 1 -and $managed.components[0].id -eq 'reshade-6.8.0') 'Allowlist skips Vortex/unmanaged packages during import'
$failure = ''
try { & $wrapper -Command Enable -ComponentId independent-qol | Out-Null } catch { $failure = $_.Exception.Message }
Assert ($failure -match 'owns only ReShade and RenoDX') 'Direct CLI cannot enable packages outside graphics ownership'
[IO.File]::WriteAllText((Join-Path $game 'qol.txt'), 'vortex-owned-fixture')
$failure = ''
try { & $wrapper -Command Profile -Profile reshade-renodx | Out-Null } catch { $failure = $_.Exception.Message }
Assert ($failure -match 'requires staged/imported component') 'Missing profile package fails before mutation'
Assert (-not (Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll'))) 'Failed group preflight leaves host disabled'
Make-Package 'renodx-cp2077-2026.0916.2204' 'bin/x64/renodx-cp2077.addon64' @('reshade-6.8.0')
& $wrapper -Command ImportStaged | Out-Null
& $wrapper -Command Profile -Profile reshade-renodx | Out-Null
Assert ((Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll')) -and (Test-Path -LiteralPath (Join-Path $game 'bin/x64/renodx-cp2077.addon64'))) 'Combined profile enables host before dependent'
[IO.File]::WriteAllText((Join-Path $game 'bin/x64/OptiScaler.ini'), 'runtime-personal-choice')
$snapshot = & $wrapper -Command Snapshot
$snap = Get-Content -LiteralPath $snapshot.snapshot -Raw | ConvertFrom-Json
Assert (@($snap.files | Where-Object path -eq 'bin/x64/OptiScaler.ini').Count -eq 1) 'Wrapper snapshot captures unowned mutable config'
& $wrapper -Command Profile -Profile reshade-only | Out-Null
Assert ((Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll')) -and -not (Test-Path -LiteralPath (Join-Path $game 'bin/x64/renodx-cp2077.addon64'))) 'ReShade-only removes only dependent visual add-on'
& $wrapper -Command Profile -Profile visuals-off | Out-Null
Assert (-not (Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll'))) 'Visuals-off disables final host'
Assert ((Get-Content -LiteralPath (Join-Path $game 'bin/x64/OptiScaler.ini') -Raw) -ceq 'runtime-personal-choice') 'Group switches preserve personal runtime config'
Assert (Test-Path -LiteralPath (Join-Path $game 'qol.txt')) 'Group switches preserve independent QoL component'
& $wrapper -Command Toggle -ComponentId reshade-6.8.0 | Out-Null
Assert (Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll')) 'Individual graphics toggle enables selected DLL'
& $wrapper -Command Toggle -ComponentId reshade-6.8.0 | Out-Null
Assert (-not (Test-Path -LiteralPath (Join-Path $game 'bin/x64/ReShade64.dll'))) 'Individual graphics toggle disables selected DLL'
Assert ((Get-Content -LiteralPath (Join-Path $game 'qol.txt') -Raw) -ceq 'vortex-owned-fixture') 'Individual graphics toggles preserve Vortex-owned data'
$manifestPath = Join-Path $base 'staging/reshade-6.8.0/component.json'
$invalid = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$invalid.files += @([pscustomobject]@{root='game';path='bin/x64/OptiScaler.ini';payload='file.txt'})
Json $manifestPath $invalid
$failure = ''
try { & $wrapper -Command ImportStaged | Out-Null } catch { $failure = $_.Exception.Message }
Assert ($failure -match 'must own only its exact DLL') 'Allowlisted ID cannot claim mutable settings or unrelated files'
[pscustomobject]@{ result='PASS';checks=$checks;scope='Private launcher fixture; only process inventory mocked';fixture=$base }
