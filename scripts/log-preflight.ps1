[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VaultRoot,

    [AllowEmptyString()]
    [string]$PendingAppend = '',

    [string]$PendingPlanFile = '',

    [ValidateScript({ $_ -gt 0 })]
    [double]$ThresholdMiB = 2,

    [datetime]$CurrentDate = (Get-Date),

    [switch]$Json,

    [switch]$Detailed
)

$ErrorActionPreference = 'Stop'

if ($PendingPlanFile) {
    if ($PendingAppend) { throw 'Use PendingAppend or PendingPlanFile, not both.' }
    $queuePlan = Get-Content -LiteralPath $PendingPlanFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($queuePlan.phase -notin @('prepared', 'appending') -or $null -eq $queuePlan.payload) {
        throw 'Expected a prepared sync plan with an exact payload.'
    }
    $PendingAppend = [string]$queuePlan.payload
}

$resolvedVaultRoot = [System.IO.Path]::GetFullPath($VaultRoot)
if (-not [System.IO.Directory]::Exists($resolvedVaultRoot)) {
    throw "Vault root does not exist: $resolvedVaultRoot"
}

$logPath = [System.IO.Path]::Combine($resolvedVaultRoot, 'log.md')
if (-not [System.IO.File]::Exists($logPath)) {
    throw "Active log does not exist: $logPath"
}

$logItem = Get-Item -LiteralPath $logPath
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$pendingBytes = [long]$utf8NoBom.GetByteCount($PendingAppend)
$thresholdBytes = [long][System.Math]::Round(
    $ThresholdMiB * 1MB,
    0,
    [System.MidpointRounding]::AwayFromZero
)
$projectedBytes = [long]$logItem.Length + $pendingBytes

$activeStartDate = $null
$reader = [System.IO.StreamReader]::new($logPath, $utf8NoBom, $true)
try {
    for ($lineNumber = 0; $lineNumber -lt 64 -and -not $reader.EndOfStream; $lineNumber++) {
        $line = $reader.ReadLine()
        if ($line -match '^## \[(\d{4}-\d{2}-\d{2})\]') {
            $parsedDate = [datetime]::MinValue
            $parsed = [datetime]::TryParseExact(
                $Matches[1],
                'yyyy-MM-dd',
                [System.Globalization.CultureInfo]::InvariantCulture,
                [System.Globalization.DateTimeStyles]::None,
                [ref]$parsedDate
            )
            if ($parsed) {
                $activeStartDate = $parsedDate.Date
            }
            break
        }
    }
}
finally {
    $reader.Dispose()
}

$sizeDue = $projectedBytes -ge $thresholdBytes
$yearDue = $null -ne $activeStartDate -and $activeStartDate.Year -lt $CurrentDate.Year
$rotationDue = $sizeDue -or $yearDue

if ($Detailed -or $rotationDue) {
    $result = [ordered]@{
        rotation_due      = [bool]$rotationDue
        size_due          = [bool]$sizeDue
        year_due          = [bool]$yearDue
        current_bytes     = [long]$logItem.Length
        pending_bytes     = [long]$pendingBytes
        projected_bytes   = [long]$projectedBytes
        threshold_bytes   = [long]$thresholdBytes
        active_start_date = if ($null -eq $activeStartDate) { $null } else { $activeStartDate.ToString('yyyy-MM-dd') }
    }
}
else {
    $result = [ordered]@{
        rotation_due = $false
        size_due     = $false
        year_due     = $false
    }
}

if ($Json) {
    [pscustomobject]$result | ConvertTo-Json -Compress
}
else {
    [pscustomobject]$result
}
