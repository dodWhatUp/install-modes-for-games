param(
    [ValidateSet('preflight','install','verify')][string]$Action='preflight',
    [string]$LabRoot,
    [string]$Bundle,
    [string]$Sha256,
    [string]$Python,
    [switch]$Upgrade
)
$ErrorActionPreference='Stop'
if(-not $Python){
    $taskBundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if(Test-Path -LiteralPath $taskBundled -PathType Leaf){$Python=$taskBundled}
    else{$taskPython=Get-Command python -ErrorAction SilentlyContinue;if($taskPython){$Python=$taskPython.Source}}
}
if(-not $Python -or -not (Test-Path -LiteralPath $Python -PathType Leaf)){throw 'Select an installed Python 3.11+ runtime with -Python. Codex may provide one through its workspace dependencies tool.'}
$taskArgs=@((Join-Path $PSScriptRoot 'portable_setup.py'),$Action)
if($LabRoot){$taskArgs+=@('--lab-root',[IO.Path]::GetFullPath($LabRoot))}
if($Action -eq 'install'){
    if(-not $LabRoot -or -not $Bundle -or -not $Sha256){throw 'Installation needs -LabRoot, -Bundle and the independently received -Sha256.'}
    $taskArgs+=@('--bundle',[IO.Path]::GetFullPath($Bundle),'--sha256',$Sha256)
    if($Upgrade){$taskArgs+='--upgrade'}
}
& $Python @taskArgs
exit $LASTEXITCODE
