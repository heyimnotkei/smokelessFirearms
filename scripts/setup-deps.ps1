# Builds the two dependency mods from source and copies their DLLs into .\external
# so this project can compile against them. Also leaves installable zips in .\deps\dist.
#
#   $env:VINTAGE_STORY = "$env:APPDATA\Vintagestory"     # folder containing VintagestoryAPI.dll
#   .\scripts\setup-deps.ps1
#
# Requires: git, dotnet SDK 10, python (on PATH as `python`)
$ErrorActionPreference = "Stop"

if (-not $env:VINTAGE_STORY) { throw "Set `$env:VINTAGE_STORY to your Vintage Story install folder (the one with VintagestoryAPI.dll)" }
if (-not (Test-Path "$env:VINTAGE_STORY\VintagestoryAPI.dll")) { throw "VintagestoryAPI.dll not found in $env:VINTAGE_STORY" }

$Root = Split-Path -Parent $PSScriptRoot
$Deps = Join-Path $Root "deps"; $Dist = Join-Path $Deps "dist"; $Ext = Join-Path $Root "external"
New-Item -ItemType Directory -Force $Deps, $Dist, $Ext | Out-Null

function Clone($url, $dir) {
    $p = Join-Path $Deps $dir
    if (Test-Path "$p\.git") { git -C $p pull --ff-only } else { git clone --depth 1 $url $p }
}

function Build($dir, $modid, $dll) {
    $project = Get-ChildItem (Join-Path $Deps $dir) -Filter *.csproj | Select-Object -First 1
    if (-not $project) { throw "No project file found under deps\$dir" }
    $out = Join-Path $Deps "$dir\bin\Release\Mods\$modid"
    Remove-Item (Join-Path $out $dll) -ErrorAction SilentlyContinue
    try { dotnet build $project.FullName -c Release -p:GameDirectory="$env:VINTAGE_STORY" -p:RunFormatter=false -p:BuildProjectReferences=false }
    catch { Write-Host "(build reported errors; checking whether the DLL was produced anyway)" }
    if (-not (Test-Path "$out\$dll")) { throw "$out\$dll was not produced. Scroll up for the compiler error." }
    $zip = Join-Path $Dist "$modid.zip"
    if (Test-Path $zip) { Remove-Item $zip }
    Compress-Archive -Path "$out\*" -DestinationPath $zip
    Copy-Item "$out\$dll" (Join-Path $Ext $dll) -Force
}

Write-Host "== Overhaul lib (legacy compat)"
Clone "https://github.com/Alodh1/Overhaullib-Legacy.git" "Overhaullib-Legacy"
Build "Overhaullib-Legacy" "overhaulliblegacycompat" "OverhaullibLegacyCompat.dll"

Write-Host "== Firearms (fork)"
Clone "https://github.com/Alodh1/Firearmsfork.git" "Firearmsfork"
$ff = Join-Path $Deps "Firearmsfork"
# Firearmsfork's project reference uses a different directory name than the clone above.
$csproj = Join-Path $ff "firearms.csproj"
$project = Get-Content $csproj -Raw
$project = $project.Replace('..\OverhaullibLegacy\Overhaullib.csproj', '..\Overhaullib-Legacy\Overhaullib.csproj')
Set-Content $csproj $project
New-Item -ItemType Directory -Force "$ff\external", "$ff\Properties" | Out-Null
Copy-Item "$Ext\OverhaullibLegacyCompat.dll", "$Deps\Overhaullib-Legacy\external\configlib.dll", "$Deps\Overhaullib-Legacy\external\PlayerModelLib.dll" "$ff\external" -Force
@"
<Project>
  <PropertyGroup>
    <RunFormatter>false</RunFormatter>
    <DataFolderName>VintagestoryData</DataFolderName>
    <GameDirectory>$env:VINTAGE_STORY</GameDirectory>
  </PropertyGroup>
</Project>
"@ | Set-Content "$ff\Properties\localSettings.props"
Build "Firearmsfork" "firearmsfork" "FirearmsFork.dll"

Write-Host ""
Write-Host "Done. DLLs for compiling are in: $Ext"
Write-Host "Install these two zips into your Vintage Story Mods folder (plus ConfigLib if you use it):"
Get-ChildItem $Dist | ForEach-Object { $_.FullName }
