$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$addonDir = Join-Path $root 'addon'
$distDir = Join-Path $root 'dist'
$manifestPath = Join-Path $addonDir 'manifest.ini'
$manifest = @{}

Get-Content -LiteralPath $manifestPath | ForEach-Object {
	if ($_ -match '^\s*([^#;][^=]+?)\s*=\s*(.+?)\s*$') {
		$manifest[$matches[1].Trim()] = $matches[2].Trim().Trim('"')
	}
}

$addonName = $manifest['name']
$version = $manifest['version']
if (-not $addonName -or -not $version) {
	throw 'manifest.ini must define name and version.'
}

$packageName = "$addonName-$version.nvda-addon"
$package = Join-Path $distDir $packageName

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
if (Test-Path -LiteralPath $package) {
	Remove-Item -LiteralPath $package -Force
}

$tempZip = Join-Path $distDir "$addonName-$version.zip"
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

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $package
"$($hash.Hash)  $packageName" | Set-Content -LiteralPath (Join-Path $distDir 'SHA256SUMS.txt') -Encoding ascii
Write-Host "Built $package"
