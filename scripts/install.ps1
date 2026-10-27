# Installs the newest Releases\smokelesslever_*.zip into the Mods folder your game actually uses.
#
#   dotnet build -c Release
#   .\scripts\install.ps1            # add -Force to skip the "is the game running" check
#
# What it does:
#   1. refuses to run while Vintage Story is open (a code mod cannot be swapped in a running game)
#   2. finds your Mods folder by locating the firearmsfork zip (works with the MVL launcher layout too)
#   3. deletes every older smokelesslever*.zip in those places, so two copies never load
#   4. copies the new zip in
param([string]$Zip, [switch]$Force)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
if (-not $Zip) {
    $latest = Get-ChildItem "$root\Releases\smokelesslever_*.zip" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw "No zip in $root\Releases. Run: dotnet build -c Release" }
    $Zip = $latest.FullName
}

if (-not $Force) {
    $running = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -like "Vintagestory*" -or $_.ProcessName -like "VintageStory*" -or
        ($_.ProcessName -eq "dotnet" -and $_.MainWindowTitle -match "Vintage")
    }
    if ($running) { throw "Vintage Story appears to be running. Quit the game AND its launcher, then run this again (or use -Force)." }
}

$searchRoots = @("$env:APPDATA\MVL", "$env:APPDATA\VintagestoryData", "$env:APPDATA\Vintagestory") | Where-Object { Test-Path $_ }

$anchor = $null
foreach ($r in $searchRoots) {
    $anchor = Get-ChildItem $r -Recurse -Filter "firearmsfork_*.zip" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($anchor) { break }
}
$dest = if ($anchor) { $anchor.DirectoryName } else { "$env:APPDATA\VintagestoryData\Mods" }
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force $dest | Out-Null }

foreach ($r in $searchRoots) {
    Get-ChildItem $r -Recurse -Filter "smokelesslever*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "removing old copy: $($_.FullName)"
        Remove-Item $_.FullName -Force
    }
}

Copy-Item $Zip $dest -Force
Write-Host ""
Write-Host "Installed $(Split-Path $Zip -Leaf) -> $dest"
Write-Host "Now start the game fresh. In client-main.log look for:  Mod 'smokelesslever_...zip' (smokelesslever)"
