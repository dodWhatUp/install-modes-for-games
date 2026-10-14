[CmdletBinding()]
param([Parameter(Mandatory)][string]$OutputDirectory,[Parameter(Mandatory)][string]$StudioDirectory,
 [Parameter(Mandatory)][string]$HubDirectory,[Parameter(Mandatory)][string]$NativeDirectory)
$ErrorActionPreference='Stop'
$taskOutput=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $taskOutput){throw 'Use a new checkpoint directory.'}
function Assert-SnapshotPath([string]$Path){
 $taskFull=[IO.Path]::GetFullPath($Path)
 if($taskFull -eq [IO.Path]::GetPathRoot($taskFull) -or $taskFull.StartsWith('\\')){throw 'Local named non-root paths only.'}
 $taskParent=$taskFull
 while($taskParent){
  if((Test-Path -LiteralPath $taskParent) -and ((Get-Item -LiteralPath $taskParent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Reparse snapshot target refused.'}
  $taskNext=Split-Path -Parent $taskParent
  if($taskNext -eq $taskParent){break};$taskParent=$taskNext
 }
 return $taskFull
}
$null=Assert-SnapshotPath $taskOutput
$taskRoots=[ordered]@{studio=$StudioDirectory;studio_settings=(Join-Path $env:APPDATA 'AzeronOverlayStudio');hub=$HubDirectory;native=$NativeDirectory}
$taskFiles=@()
foreach($taskName in $taskRoots.Keys){
 $taskRoot=Assert-SnapshotPath $taskRoots[$taskName]
 if(!(Test-Path -LiteralPath $taskRoot -PathType Container)){throw "Missing required snapshot root: $taskName"}
 foreach($taskFile in Get-ChildItem -LiteralPath $taskRoot -File -Recurse -Force){
  $null=Assert-SnapshotPath $taskFile.FullName
  $taskFiles+=@{path=$taskFile.FullName;category=$taskName;relative=$taskFile.FullName.Substring($taskRoot.Length).TrimStart('\');bytes=$taskFile.Length;sha256=(Get-FileHash -LiteralPath $taskFile.FullName).Hash;modified_utc=$taskFile.LastWriteTimeUtc.ToString('O')}
 }
}
if($taskFiles.Count -gt 2500 -or ($taskFiles|Measure-Object bytes -Sum).Sum -gt 268435456){throw 'Bounded snapshot limit exceeded; inspect before copying.'}
New-Item -ItemType Directory -Path $taskOutput | Out-Null
foreach($taskRow in $taskFiles){
 $taskCopy=Join-Path (Join-Path $taskOutput $taskRow.category) $taskRow.relative
 New-Item -ItemType Directory -Path (Split-Path -Parent $taskCopy) -Force | Out-Null
 Copy-Item -LiteralPath $taskRow.path -Destination $taskCopy
 if((Get-FileHash -LiteralPath $taskCopy).Hash -ne $taskRow.sha256 -or (Get-FileHash -LiteralPath $taskRow.path).Hash -ne $taskRow.sha256){throw 'Concurrent change or copied-byte mismatch; preserve checkpoint.'}
 $taskRow.copy=$taskCopy
}
$taskReceipt=@{schema_version=1;created_utc=[DateTime]::UtcNow.ToString('O');coverage='Scoped installed Studio/settings, Hub registry/assets and native storage; byte-verified copies. Not whole-system/onboard/game recovery.';restore_tested=$false;files=$taskFiles}
[IO.File]::WriteAllText((Join-Path $taskOutput 'BEFORE.json'),($taskReceipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{checkpoint=$taskOutput;files=$taskFiles.Count;copied_and_current_hash_verified=$true;native_files=@($taskFiles|Where-Object category -eq native).Count} | ConvertTo-Json
