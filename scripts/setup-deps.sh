#!/usr/bin/env bash
# Builds the two dependency mods from source and copies their DLLs into ./external
# so this project can compile against them. Also leaves installable zips in ./deps/dist.
#
#   export VINTAGE_STORY=/path/to/your/vintagestory      # folder containing VintagestoryAPI.dll
#   ./scripts/setup-deps.sh
#
# Requires: git, dotnet SDK 10, python3
set -euo pipefail

: "${VINTAGE_STORY:?Set VINTAGE_STORY to your Vintage Story install folder (the one with VintagestoryAPI.dll)}"
[ -f "$VINTAGE_STORY/VintagestoryAPI.dll" ] || { echo "VintagestoryAPI.dll not found in $VINTAGE_STORY"; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPS="$ROOT/deps"; DIST="$DEPS/dist"; EXT="$ROOT/external"
mkdir -p "$DEPS" "$DIST" "$EXT"

# The dependency csproj files shell out to `python` for zipping; make sure that name exists.
SHIM="$(mktemp -d)"; ln -s "$(command -v python3)" "$SHIM/python"; export PATH="$SHIM:$PATH"

clone() { # url dir
  if [ -d "$DEPS/$2/.git" ]; then git -C "$DEPS/$2" pull --ff-only; else git clone --depth 1 "$1" "$DEPS/$2"; fi
}

build() { # dir modid dll
  ( cd "$DEPS/$1"
    dotnet build -c Release -p:GameDirectory="$VINTAGE_STORY" -p:RunFormatter=false || echo "(build reported errors; checking whether the DLL was produced anyway)"
  )
  local out="$DEPS/$1/bin/Release/Mods/$2"
  [ -f "$out/$3" ] || { echo "ERROR: $out/$3 was not produced. Scroll up for the compiler error."; exit 1; }
  python3 - "$out" "$DIST/$2.zip" <<'PY'
import os, sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for r, _, fs in os.walk(src):
        for f in fs:
            p = os.path.join(r, f); z.write(p, os.path.relpath(p, src).replace(os.sep, "/"))
PY
  cp "$out/$3" "$EXT/$3"
}

echo "== Overhaul lib (legacy compat)"
clone https://github.com/Alodh1/Overhaullib-Legacy.git Overhaullib-Legacy
build Overhaullib-Legacy overhaulliblegacycompat OverhaullibLegacyCompat.dll

echo "== Firearms (fork)"
clone https://github.com/Alodh1/Firearmsfork.git Firearmsfork
mkdir -p "$DEPS/Firearmsfork/external" "$DEPS/Firearmsfork/Properties"
cp "$EXT/OverhaullibLegacyCompat.dll" "$DEPS/Overhaullib-Legacy/external/configlib.dll" "$DEPS/Overhaullib-Legacy/external/PlayerModelLib.dll" "$DEPS/Firearmsfork/external/"
cat > "$DEPS/Firearmsfork/Properties/localSettings.props" <<EOF
<Project>
  <PropertyGroup>
    <RunFormatter>false</RunFormatter>
    <DataFolderName>VintagestoryData</DataFolderName>
    <GameDirectory>$VINTAGE_STORY</GameDirectory>
  </PropertyGroup>
</Project>
EOF
build Firearmsfork firearmsfork FirearmsFork.dll

echo
echo "Done. DLLs for compiling are in: $EXT"
echo "Install these two zips into your Vintage Story Mods folder (plus ConfigLib if you use it):"
ls -1 "$DIST"
