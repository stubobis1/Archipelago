#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ReqFile = "vendor_requirements.txt"
$OutDir  = "vendor_modules"
$ZipFile = "vendor_modules.zip"

# Find Python (prefer 'py', then 'python') without ?. (PowerShell 7 only)
$pythonCmd = $null

$cmd = Get-Command py -ErrorAction SilentlyContinue
if ($cmd) { $pythonCmd = $cmd.Source }

if (-not $pythonCmd) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $pythonCmd = $cmd.Source }
}

if (-not $pythonCmd) { throw "python/py not found on PATH." }
if (-not (Test-Path -LiteralPath $ReqFile)) { throw "$ReqFile not found." }

# Clean previous outputs
if (Test-Path -LiteralPath $OutDir)  { Remove-Item -LiteralPath $OutDir -Recurse -Force }
if (Test-Path -LiteralPath $ZipFile) { Remove-Item -LiteralPath $ZipFile -Force }

# Install into a target folder (includes transitive deps)
& $pythonCmd -m pip install `
  --upgrade `
  --no-cache-dir `
  -r $ReqFile `
  -t $OutDir

# Optional: prune __pycache__
Get-ChildItem -Path $OutDir -Directory -Recurse -Filter "__pycache__" |
  Remove-Item -Recurse -Force

# Zip results
Compress-Archive -Path (Join-Path $OutDir '*') -DestinationPath $ZipFile -Force

# Remove vendor_modules after zipping
if (Test-Path -LiteralPath $OutDir) {
    Remove-Item -LiteralPath $OutDir -Recurse -Force
}

Write-Host "Done:"
Write-Host "  Zipped as: $ZipFile"
