[CmdletBinding()]
param([Parameter(Mandatory)][string]$AccessReceipt)
# Explicit shortcut preparation only: never starts the app or enables input.
$ErrorActionPreference = 'Stop'
$taskReceiptPath = [IO.Path]::GetFullPath($AccessReceipt)
$taskAccess = Get-Content -LiteralPath $taskReceiptPath -Raw | ConvertFrom-Json
if ($taskAccess.schema_version -ne 1 -or $taskAccess.app_launched -ne $false) { throw 'Unsupported access receipt.' }
$taskRuntime = [IO.Path]::GetFullPath($taskAccess.runtime)
$taskLauncher = [IO.Path]::GetFullPath($taskAccess.launcher)
$taskRoot = [IO.Path]::GetFullPath($taskAccess.working_directory)
if ([IO.Path]::GetFileName($taskRuntime) -ine 'pythonw.exe' -or
    [IO.Path]::GetFileName($taskLauncher) -ine 'Start-UnifiedTools.pyw' -or
    [IO.Path]::GetDirectoryName($taskLauncher) -ine $taskRoot) { throw 'Unexpected launcher paths.' }
if (!(Test-Path -LiteralPath $taskRuntime -PathType Leaf) -or
    !(Test-Path -LiteralPath $taskLauncher -PathType Leaf)) { throw 'Verified launcher/runtime missing.' }
$taskInstall = Get-Content -LiteralPath (Join-Path $taskRoot 'install.json') -Raw | ConvertFrom-Json
if ($taskInstall.current -ne $taskAccess.version -or
    (Get-FileHash -LiteralPath $taskLauncher -Algorithm SHA256).Hash -ine $taskInstall.bootstrap_sha256) { throw 'Launcher/version changed; inspect again.' }
$taskDesktop = [Environment]::GetFolderPath('Desktop')
if (!(Test-Path -LiteralPath $taskDesktop -PathType Container)) { throw 'Desktop folder unavailable.' }
$taskShortcutPath = Join-Path $taskDesktop 'Unified Game Tools.lnk'
$taskArguments = '-B "' + $taskLauncher + '"'
$taskShell = New-Object -ComObject WScript.Shell
$taskShortcut = $taskShell.CreateShortcut($taskShortcutPath)
$taskCreated = $false
if (Test-Path -LiteralPath $taskShortcutPath) {
    if ($taskShortcut.TargetPath -ine $taskRuntime -or $taskShortcut.Arguments -cne $taskArguments -or
        $taskShortcut.WorkingDirectory -ine $taskRoot) { throw 'Existing shortcut differs; preserve it.' }
} else {
    $taskShortcut.TargetPath = $taskRuntime
    $taskShortcut.Arguments = $taskArguments
    $taskShortcut.WorkingDirectory = $taskRoot
    $taskShortcut.Description = 'Open the installed Unified Game Tools. No reinstall; Game Input starts Off.'
    $taskShortcut.IconLocation = $taskRuntime + ',0'
    $taskShortcut.WindowStyle = 1
    $taskShortcut.Save()
    $taskCreated = $true
}
$taskReadback = $taskShell.CreateShortcut($taskShortcutPath)
if (!(Test-Path -LiteralPath $taskShortcutPath -PathType Leaf) -or
    $taskReadback.TargetPath -ine $taskRuntime -or $taskReadback.Arguments -cne $taskArguments -or
    $taskReadback.WorkingDirectory -ine $taskRoot) { throw 'Shortcut readback differs.' }
$taskResult = [ordered]@{ shortcut = $taskShortcutPath; created = $taskCreated;
    target_verified = $true; arguments_verified = $true; app_launched = $false;
    shortcut_sha256 = (Get-FileHash -LiteralPath $taskShortcutPath -Algorithm SHA256).Hash }
$taskResultPath = Join-Path ([IO.Path]::GetDirectoryName($taskReceiptPath)) 'SHORTCUT.json'
[IO.File]::WriteAllText($taskResultPath, ($taskResult | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
$taskResult | ConvertTo-Json
