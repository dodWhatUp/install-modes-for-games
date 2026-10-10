#Requires -Version 7.0
param(
 [Parameter(Mandatory)][int]$GameProcessId,
 [Parameter(Mandatory)][string]$OutputDirectory,
 [ValidateRange(5,7200)][int]$Seconds=90,
 [ValidateRange(500,10000)][int]$IntervalMs=1000
)
$ErrorActionPreference='Stop'
# Read-only telemetry. Does not change clocks, power limits, game files or hooks.
$out=[IO.Path]::GetFullPath($OutputDirectory)
if(Test-Path -LiteralPath $out){throw 'Use a new run directory to preserve previous captures.'}
[IO.Directory]::CreateDirectory($out)|Out-Null
$target=Get-Process -Id $GameProcessId
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class GameResourceNative {
 [StructLayout(LayoutKind.Sequential)]
 public struct MemoryStatus {
  public uint Length, Load;
  public ulong TotalPhysical, AvailablePhysical, TotalPageFile, AvailablePageFile, TotalVirtual, AvailableVirtual, AvailableExtendedVirtual;
 }
 [StructLayout(LayoutKind.Sequential)]
 public struct PerformanceInfo {
  public uint Size;
  public UIntPtr CommitTotal, CommitLimit, CommitPeak, PhysicalTotal, PhysicalAvailable, SystemCache, KernelTotal, KernelPaged, KernelNonpaged, PageSize;
  public uint HandleCount, ProcessCount, ThreadCount;
 }
 [DllImport("kernel32.dll", SetLastError=true)]
 public static extern bool GlobalMemoryStatusEx(ref MemoryStatus value);
 [DllImport("psapi.dll", SetLastError=true)]
 public static extern bool GetPerformanceInfo(ref PerformanceInfo value, uint size);
 [DllImport("kernel32.dll", SetLastError=true)]
 public static extern bool GetSystemTimes(out ulong idle, out ulong kernel, out ulong user);
 public static MemoryStatus Memory() {
  var value=new MemoryStatus(); value.Length=(uint)Marshal.SizeOf(value);
  if(!GlobalMemoryStatusEx(ref value)) throw new System.ComponentModel.Win32Exception(); return value;
 }
 public static PerformanceInfo Performance() {
  var value=new PerformanceInfo(); value.Size=(uint)Marshal.SizeOf(value);
  if(!GetPerformanceInfo(ref value,value.Size)) throw new System.ComponentModel.Win32Exception(); return value;
 }
 public static ulong[] Cpu() {
  ulong idle,kernel,user; if(!GetSystemTimes(out idle,out kernel,out user)) throw new System.ComponentModel.Win32Exception();
  return new ulong[]{idle,kernel,user};
 }
}
'@
$query='memory.total,memory.reserved,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit,clocks.gr,clocks.mem,pstate,clocks_event_reasons.active,clocks_event_reasons.sw_power_cap,clocks_event_reasons.hw_thermal_slowdown'
$begin=[DateTime]::UtcNow
$clock=[Diagnostics.Stopwatch]::StartNew()
$rows=[Collections.Generic.List[object]]::new()
$previousCpu=$target.TotalProcessorTime.TotalSeconds
$previousTime=0.0
$logicalCpu=[Environment]::ProcessorCount
$previousSystemCpu=[GameResourceNative]::Cpu()
$collectorSelf=Get-Process -Id $PID
$previousCollectorCpu=$collectorSelf.TotalProcessorTime.TotalSeconds
function NumberOrNull($value){
 $parsed=0.0
 if([double]::TryParse([string]$value,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$parsed)){return $parsed}
 return $null
}
while($clock.Elapsed.TotalSeconds-lt$Seconds){
 $sampleStart=$clock.Elapsed.TotalMilliseconds
 $physical=[GameResourceNative]::Memory()
 $commit=[GameResourceNative]::Performance()
 $systemCpu=[GameResourceNative]::Cpu()
 $cpuTotalDelta=([double]$systemCpu[1]+[double]$systemCpu[2])-([double]$previousSystemCpu[1]+[double]$previousSystemCpu[2])
 $systemCpuPercent=if($cpuTotalDelta-gt0){100*(1-([double]$systemCpu[0]-[double]$previousSystemCpu[0])/$cpuTotalDelta)}else{$null}
 $previousSystemCpu=$systemCpu
 $gpuText=(& nvidia-smi "--query-gpu=$query" --format=csv,noheader,nounits 2> (Join-Path $out 'gpu-query-error.txt'))
 $gpuExit=$LASTEXITCODE
 $gpu=@(([string]($gpuText|Select-Object -First 1)) -split ',\s*')
 if($gpuExit-ne0 -or $gpu.Count-ne15){$gpu=@($null)*15}
 $game=Get-Process -Id $GameProcessId -ErrorAction SilentlyContinue
 $now=$clock.Elapsed.TotalSeconds
 $collectorSelf.Refresh()
 $collectorCpuPercent=if($now-gt$previousTime){100*($collectorSelf.TotalProcessorTime.TotalSeconds-$previousCollectorCpu)/($now-$previousTime)}else{$null}
 $previousCollectorCpu=$collectorSelf.TotalProcessorTime.TotalSeconds
 $cpuPercent=$null
 if($game){
  if($now-gt$previousTime){$cpuPercent=100*($game.TotalProcessorTime.TotalSeconds-$previousCpu)/($now-$previousTime)/$logicalCpu}
  $previousCpu=$game.TotalProcessorTime.TotalSeconds
 }
 $previousTime=$now
 $row=[ordered]@{
  utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();qpcFrequency=[Diagnostics.Stopwatch]::Frequency
  elapsedSeconds=[Math]::Round($now,3);processAlive=($null-ne$game);responding=if($game){$game.Responding}else{$false}
  processCpuPercentAllCores=$cpuPercent
  collectorCpuPercentOneCore=$collectorCpuPercent
  collectorWorkingSetMiB=$collectorSelf.WorkingSet64/1MB
  processWorkingSetMiB=if($game){$game.WorkingSet64/1MB}else{$null}
  processPrivateCommitMiB=if($game){$game.PrivateMemorySize64/1MB}else{$null}
  processVirtualAddressMiB=if($game){$game.VirtualMemorySize64/1MB}else{$null}
  systemRamTotalMiB=[double]$physical.TotalPhysical/1MB
  systemRamAvailableMiB=[double]$physical.AvailablePhysical/1MB
  systemRamUnavailableMiB=([double]$physical.TotalPhysical-[double]$physical.AvailablePhysical)/1MB
  systemCommitMiB=[double]$commit.CommitTotal.ToUInt64()*$commit.PageSize.ToUInt64()/1MB
  systemCommitLimitMiB=[double]$commit.CommitLimit.ToUInt64()*$commit.PageSize.ToUInt64()/1MB
  systemPagesInputPerSec=$null
  systemCpuPercent=$systemCpuPercent
  busiestLogicalCpuPercent=$null
  gpuTotalMiB=NumberOrNull $gpu[0];gpuDriverReservedMiB=NumberOrNull $gpu[1]
  gpuUsedMiB=NumberOrNull $gpu[2];gpuFreeMiB=NumberOrNull $gpu[3]
  gpuPercent=NumberOrNull $gpu[4];gpuMemoryControllerPercent=NumberOrNull $gpu[5]
  gpuTemperatureC=NumberOrNull $gpu[6];gpuPowerW=NumberOrNull $gpu[7];gpuPowerLimitW=NumberOrNull $gpu[8]
  gpuClockMHz=NumberOrNull $gpu[9];gpuMemoryClockMHz=NumberOrNull $gpu[10];gpuPstate=$gpu[11]
  gpuClockEventReasons=$gpu[12];gpuSoftwarePowerCap=$gpu[13];gpuHardwareThermalSlowdown=$gpu[14]
  gpuQueryExitCode=$gpuExit
 }
 $row['collectionMilliseconds']=$clock.Elapsed.TotalMilliseconds-$sampleStart
 $rows.Add([pscustomobject]$row)
 $remaining=$IntervalMs-($clock.Elapsed.TotalMilliseconds-$sampleStart)
 if($remaining-gt0){Start-Sleep -Milliseconds ([int]$remaining)}
}
$rows|Export-Csv -LiteralPath (Join-Path $out 'resources.csv') -NoTypeInformation
[ordered]@{
 schemaVersion=1;beginUtc=$begin.ToString('o');endUtc=[DateTime]::UtcNow.ToString('o');gameProcessId=$GameProcessId
 targetName=$target.ProcessName;samples=$rows.Count;requestedSeconds=$Seconds;intervalMs=$IntervalMs
 qpcFrequency=[Diagnostics.Stopwatch]::Frequency
 limitations=@('GPU readings cover the entire adapter, not only the game.','Driver-reserved memory is not game-requested reservation or its WDDM budget.','Unavailable RAM includes caches/other processes; private commit is not resident RAM.','Per-core CPU, paging and I/O counters are unavailable in this minimal collector.','CPU sampling cannot prove the frame bottleneck.','No per-frame timings or physical input-to-photon latency in this resource file.')
}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $out 'capture.json')
Get-Content -LiteralPath (Join-Path $out 'capture.json')
