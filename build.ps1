$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$addonDir = Join-Path $root 'addon'
$distDir = Join-Path $root 'dist'
$package = Join-Path $distDir 'wenxingBraille-0.1.0.nvda-addon'

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
if (Test-Path -LiteralPath $package) {
	Remove-Item -LiteralPath $package -Force
}

$tempZip = Join-Path $distDir 'wenxingBraille-0.1.0.zip'
if (Test-Path -LiteralPath $tempZip) {
	Remove-Item -LiteralPath $tempZip -Force
}

$staging = Join-Path $distDir 'staging'
if (Test-Path -LiteralPath $staging) {
	Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Get-ChildItem -LiteralPath $addonDir -Force | ForEach-Object {
	Copy-Item -LiteralPath $_.FullName -Destination $staging -Recurse -Force
}
Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' | ForEach-Object {
	Remove-Item -LiteralPath $_.FullName -Recurse -Force
}
Get-ChildItem -Path $staging -Recurse -Include '*.pyc', '*.pyo' -File | ForEach-Object {
	Remove-Item -LiteralPath $_.FullName -Force
}

Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $tempZip -Force
Move-Item -LiteralPath $tempZip -Destination $package -Force
Remove-Item -LiteralPath $staging -Recurse -Force
Write-Host "Built $package"
