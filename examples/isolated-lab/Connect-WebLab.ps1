param(
    [Parameter(Mandatory=$true)][string]$Plan,
    [ValidateSet('init','doctor','run')][string]$Action = 'doctor',
    [string]$TunnelId
)
$ErrorActionPreference = 'Stop'
$webPlan = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
if ($webPlan.schema -ne 1) { throw 'Unsupported web plan' }
$webClient = $webPlan.client
if ((Get-FileHash -LiteralPath $webClient -Algorithm SHA256).Hash.ToLower() -ne $webPlan.client_sha256) {
    throw 'Tunnel executable changed; verify before use'
}
$webFolder = Split-Path -Parent (Resolve-Path -LiteralPath $Plan).Path
foreach ($webName in @('web_mcp.py','Connect-WebLab.ps1')) {
    $webHash = (Get-FileHash -LiteralPath (Join-Path $webFolder $webName) -Algorithm SHA256).Hash.ToLower()
    if ($webHash -ne $webPlan.source_sha256.$webName) { throw 'Prepared source changed; reconcile plan' }
}
if ($Action -eq 'init') {
    if ($TunnelId -notmatch '^tunnel_[A-Za-z0-9_-]+$') { throw 'Supply the full tunnel ID returned by Platform' }
    & $webClient init --sample sample_mcp_stdio_local --profile $webPlan.profile --profile-dir $webPlan.profile_dir `
        --tunnel-id $TunnelId --mcp-command $webPlan.mcp_command --health-listen-addr '127.0.0.1:0'
    if ($LASTEXITCODE -ne 0) { throw 'Profile initialization failed; inspect before retrying' }
    return
}
$webPreviousKey = $env:CONTROL_PLANE_API_KEY
$webSecureKey = $null
$webKeyPointer = [IntPtr]::Zero
try {
    if (-not $env:CONTROL_PLANE_API_KEY) {
        $webSecureKey = Read-Host 'Runtime API key for this private tunnel (input hidden; not saved)' -AsSecureString
        $webKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($webSecureKey)
        $env:CONTROL_PLANE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($webKeyPointer)
    }
    if ($Action -eq 'doctor') {
        & $webClient doctor --profile $webPlan.profile --profile-dir $webPlan.profile_dir --explain
    } else {
        # Foreground, operator-selected runtime. Does not open a browser or touch desktop input.
        & $webClient run --profile $webPlan.profile --profile-dir $webPlan.profile_dir `
            --mcp.max-concurrent-requests 1 --control-plane.max-inflight 1
    }
    if ($LASTEXITCODE -ne 0) { throw 'Tunnel client failed; inspect diagnostics before reconnecting' }
} finally {
    $env:CONTROL_PLANE_API_KEY = $webPreviousKey
    if ($webKeyPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($webKeyPointer) }
    if ($webSecureKey) { $webSecureKey.Dispose() }
}
