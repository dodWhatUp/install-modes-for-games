param(
    [Parameter(Mandatory=$true)][string]$LabRoot,
    [switch]$Install
)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath($LabRoot).TrimEnd('\')
if($taskRoot -eq [IO.Path]::GetPathRoot($taskRoot)){throw 'Choose a dedicated lab directory'}
$taskInstaller=Join-Path $taskRoot 'downloads\VirtualBox-7.2.20-175154-Win.exe'
$taskMsi=Join-Path $taskRoot 'downloads\VirtualBox-7.2.20-r175154-MultiArch_amd64.msi'
$taskSums=Join-Path $taskRoot 'downloads\VirtualBox-SHA256SUMS'
$taskReceipt=Join-Path $taskRoot 'private\downloads-receipt.json'
foreach($taskFile in @($taskInstaller,$taskMsi,$taskSums,$taskReceipt)){
    if(-not (Test-Path -LiteralPath $taskFile -PathType Leaf)){throw "Missing prepared file: $taskFile"}
}
$taskExpected=((Get-Content -LiteralPath $taskSums|Where-Object {$_ -match 'VirtualBox-7.2.20-175154-Win.exe$'}) -split '\s+')[0]
if((Get-FileHash -LiteralPath $taskInstaller -Algorithm SHA256).Hash -ne $taskExpected){throw 'Official installer hash mismatch'}
$taskDownloads=Get-Content -LiteralPath $taskReceipt -Raw|ConvertFrom-Json
if((Get-FileHash -LiteralPath $taskMsi -Algorithm SHA256).Hash -ne $taskDownloads.virtualbox_msi_sha256){throw 'Prepared MSI hash mismatch'}
foreach($taskFile in @($taskInstaller,$taskMsi)){
    $taskSignature=Get-AuthenticodeSignature -LiteralPath $taskFile
    if($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notmatch 'Oracle America, Inc.'){
        throw 'Expected a valid Oracle signature'
    }
}
$taskFirmware=(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled
$taskPreflight=[ordered]@{FirmwareVirtualizationEnabled=$taskFirmware;InstallerVerified=$true;Mode='Prepared only';Features='VBoxApplication only; NAT, no USB/bridged/host-only/Python drivers';AutomaticReboot=$false}
if(-not $Install){$taskPreflight|ConvertTo-Json; exit 0}
if(-not $taskFirmware){throw 'Enable SVM Mode in BIOS/UEFI first; installation was not started'}
if(Test-Path -LiteralPath 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'){
    throw 'VirtualBox is already installed. Inspect its version/configuration rather than reinstalling it.'
}
$taskLog=Join-Path $taskRoot 'private\virtualbox-install.log'
$taskArguments='/i "'+$taskMsi+'" /qn /norestart ADDLOCAL=VBoxApplication VBOX_START=0 VBOX_INSTALLDESKTOPSHORTCUT=0 VBOX_INSTALLQUICKLAUNCHSHORTCUT=0 VBOX_REGISTERFILEEXTENSIONS=0 REBOOT=ReallySuppress /L*v "'+$taskLog+'"'
$taskProcess=Start-Process -FilePath 'msiexec.exe' -ArgumentList $taskArguments -Verb RunAs -WindowStyle Hidden -Wait -PassThru
if($taskProcess.ExitCode -notin @(0,3010)){throw "Installation failed with exit $($taskProcess.ExitCode); inspect $taskLog"}
$taskPreflight.Mode='Installer finished; VM boot acceptance still pending'
$taskPreflight.ExitCode=$taskProcess.ExitCode
$taskPreflight.RebootRequired=($taskProcess.ExitCode -eq 3010)
$taskPreflight|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskRoot 'private\virtualbox-install-receipt.json')
$taskPreflight|ConvertTo-Json
