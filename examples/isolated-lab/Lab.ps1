param(
    [ValidateSet('status','start','wait-ready','run','screenshot','fetch','stop','force-stop','checkpoint','restore')]
    [string]$Action='status',
    [ValidateSet('linux','windows')][string]$Guest='linux',
    [string]$Script,
    [int]$Timeout=120,
    [string]$Name,
    [string]$Checkpoint,
    [string]$LabRoot=$PSScriptRoot
)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath($LabRoot)
$taskRuntime=Get-Content -LiteralPath (Join-Path $taskRoot 'private\runtime.json') -Raw|ConvertFrom-Json
$taskConfig=Join-Path $taskRoot 'private\config.json'
$taskCode=Join-Path $taskRoot 'source\examples\isolated-lab\lab.py'
foreach($taskFile in @($taskRuntime.python,$taskConfig,$taskCode)){
    if(-not (Test-Path -LiteralPath $taskFile -PathType Leaf)){throw "Missing lab dependency: $taskFile"}
}
$taskArguments=@($taskCode,'--config',$taskConfig,$Action)
if($Action -ne 'status'){$taskArguments+=@($Guest)}
switch($Action){
    'wait-ready' {$taskArguments+=@('--timeout',[string]$Timeout)}
    'run' {
        if(-not $Script){throw 'Select a guest script with -Script'}
        $taskArguments+=@('--script',[IO.Path]::GetFullPath($Script),'--timeout',[string]$Timeout)
    }
    'fetch' {
        if(-not $Name){throw 'Select a guest artifacts filename with -Name'}
        $taskArguments+=@('--name',$Name)
    }
    'checkpoint' {
        if(-not $Name){throw 'Select a new checkpoint label with -Name'}
        $taskArguments+=@('--name',$Name)
    }
    'restore' {
        if(-not $Checkpoint){throw 'Select a checkpoint directory with -Checkpoint'}
        $taskArguments+=@('--checkpoint',[IO.Path]::GetFullPath($Checkpoint))
    }
}
& $taskRuntime.python @taskArguments
exit $LASTEXITCODE
