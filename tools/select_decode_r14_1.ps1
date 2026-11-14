param([ValidateSet("baseline","matrix")][string]$Variant)
$ErrorActionPreference = "Stop"
try {
    $root = $env:R14_COMPARE_ROOT
    if (-not $root) { throw "Run USE_R14_DECODE.cmd or USE_MATRIX_DECODE.cmd" }
    $m = Get-Content -LiteralPath (Join-Path $root "doc/R14_1_DECODE_VARIANTS.json") -Raw | ConvertFrom-Json
    $target = Join-Path $root $m.active
    $allowed = @()
    foreach ($name in @("baseline", "matrix")) {
        $v = $m.variants.$name
        $h = (Get-FileHash -LiteralPath (Join-Path $root $v.path) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($h -ne $v.sha256) { throw "Saved variant changed; selection refused" }
        $allowed += $h
    }
    $current = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($current -notin $allowed) { throw "Active decoder has user edits; selection refused" }
    Copy-Item -LiteralPath (Join-Path $root $m.variants.$Variant.path) -Destination $target
    $result = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($result -ne $m.variants.$Variant.sha256) { throw "Copy verification failed" }
    Write-Output "Selected $Variant. Rebuild in GOWIN before programming the FPGA."
} catch { Write-Error $_; exit 1 }
