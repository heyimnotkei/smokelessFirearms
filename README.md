# Smokeless Firearms (`smokelessfirearms`)

Addon for **Vintage Story 1.22.x** that adds:

| Item | Notes |
|---|---|
| **Guncotton** + **Smokeless powder** | Barrel-crafted chain: fibre + saltpeter + sulfur + water → guncotton; guncotton + spirits → smokeless powder |
| **.30-30 style cartridge** (lead / copper bullet) | Brass case + primer + smokeless powder + bullet. Projectile leaves **no smoke trail** |
| **Lever-action carbine** (Model 1894 style) | Side-loading gate, 6 in the tube + 1 chambered (`MagazineSize` 7), lever cycles automatically after each shot |
| **Break-action shotguns** | Single and double-barrel models hinge open to load buckshot or slug shells; each shell takes 2550 ms to load. |
| **Rolling-block rifle (.50)** | Single-shot rear-loader with a 5500 ms reload, 75 piercing damage, and 1 MOA dispersion. |

Built on **Firearmsfork** (Alodh1) which runs on **Overhaul lib – legacy compat** (Alodh1). Note that
`maltiez2/vsmod_overhaullib_2` (2.0.x) is currently only a small utility library (no ranged weapons,
animation or input systems), so it cannot host a firearm yet; the legacy-compat lib is the one that
works on 1.22.x.

## Build

Prereqs: Vintage Story 1.22.x and **.NET SDK 10**. Copy `FirearmsFork.dll` and `OverhaullibLegacyCompat.dll` into `external/` before building.

```bash
# 1. point at your game folder (the one containing VintagestoryAPI.dll)
export VINTAGE_STORY=/path/to/vintagestory          # Windows PowerShell: $env:VINTAGE_STORY="$env:APPDATA\Vintagestory"

# 2. build this mod  ->  Releases/smokelessfirearms_1.8.3.zip
dotnet build -c Release
```

For each subsequent update, increment the patch number in `ModVersion` (for example, `1.8.4`, then `1.8.5`) before building.

## Install

Download a mod zip from the [GitHub Releases page](https://github.com/heyimnotkei/smokelessFirearms/releases) and copy it into your Vintage Story Mods folder. Quit the game and launcher before replacing a code mod. Install these dependencies in the same Mods folder:

* `overhaulliblegacycompat.zip`
* `firearmsfork.zip`

(ConfigLib and VSImGui are used by those mods; keep them installed.)

Your game logs the folders it searches at startup (`Will search the following paths for mods:` in `client-main.log`).

## Controls

* **Hold RMB when empty**: load one cartridge per pass through the side gate until the tube is full. Release early to keep what is loaded; reload only after the rifle is empty.
* **Hold RMB again**: work the lever to chamber a round, then keep holding to aim. **LMB** fires; the lever cycles automatically.
* **Alt** = interact instead of aim/reload (same as the other firearms).
* Both shotguns reload only when empty and open at the breech to load shells one at a time (2550 ms per shell). The double barrel holds two.
* The rolling block opens its breech for a 5500 ms reload and accepts only .50 heavy cartridges.

## Crafting

| Result | Recipe |
|---|---|
| Guncotton ×4 | Crafting grid, one row: 4 flax fibres + saltpeter + sulfur |
| Smokeless powder ×16 | Barrel (sealed 12 h): 8 guncotton + 1 L spirits (a barrel takes only one item + one liquid) |
| Brass case ×4 | Hammer + brass plate |
| Primer ×6 | Hammer + brass plate + blasting powder |
| Cartridge ×4 | 4 case + 4 primer + 2 smokeless powder + 4 bullets (`maltiezfirearms:bullet-lead` or `-copper`) |
| Shotgun casing ×4 | Hammer + brass plate |
| Buckshot shells ×4 | 4 shotgun casings + 4 primers + 2 smokeless powder + 32 lead pellets (`maltiezfirearms:pellet-lead`) |
| Slug shells ×4 | 4 shotgun casings + 4 primers + 2 smokeless powder + 4 lead slugs (`maltiezfirearms:slug-lead`) |
| .50 heavy cartridges ×4 | 4 brass cases + 4 primers + 2 smokeless powder + 4 lead bullets; use the rolling-block mechanism as a reusable tool |
| Firing-mechanism parts | Steel plates, brass plate, steel nails-and-strips, rusty gear; craft trigger/sear, firing pin, and mainspring separately |
| Firing mechanisms | Assemble each unique mechanism from its parts with Gun Smith's blueprints as a reusable tool |
| Lever-action carbine | Steel plates ×3, Firearms carbine barrel, steel nails-and-strips ×2, plank, rusty gear, and lever-action mechanism |
| Single-loading shotgun | Steel plates ×3, Firearms carbine barrel, steel nails-and-strips ×2, plank, rusty gear, and break-action mechanism |
| Double-barrel shotgun | Two Firearms carbine barrels, steel plate, steel nails-and-strips ×2, planks ×2, rusty gear, and break-action mechanism |
| Rolling-block rifle | Steel plates ×3, Firearms carbine barrel, steel nails-and-strips ×2, plank, rusty gear, and rolling-block mechanism |

The blueprints and mechanisms are available in creative inventory. The blueprint is reusable and required to craft any of the three unique firing mechanisms. Ammo recipes use their matching mechanism as a reusable tool.

## Things I could not test (no game available where this was written)

I compiled `source/*.cs` against the official 1.22.7 API sources plus the current Overhaullib-Legacy and
Firearmsfork sources with a Roslyn semantic check (clean: 0 errors). The JSON was validated for syntax, but
**nothing has been run in the game**. Expect to tune:

1. **Lever / gate swing direction** – adjust the relevant rotations in
   `resources/assets/smokelessfirearms/config/animations/leveraction.json`.
2. **Arm poses** – reused from the fork's carbine (loading uses its "prime" pose, near the receiver). Adjust in
   `resources/assets/smokelessfirearms/config/animations/leveraction.json`. `BulletTransform` (the cartridge shown at
   the gate while loading) in `itemtypes/leveraction.json` will likely need nudging.
3. **Base-game item codes** used in recipes: confirmed from the fork's own recipes / official source: `game:saltpeter`,
   `game:powder-sulfur`, `game:blastingpowder`, `game:metalplate-brass`, `game:metalplate-steel`,
   `game:metalnailsandstrips-steel`, `game:plank-*`, `game:gear-rusty`, `game:waterportion`, `game:flaxfibers`.
   **Not confirmed:** `game:spiritportion` and `game:hammer-*`. A wrong code only logs a recipe warning at load;
   fix the code in the matching recipe JSON under `resources/assets/smokelessfirearms/recipes/`.
4. **Balance** – damage/velocity are set just above the fork's musket (`BulletDamageStrength` 9, `BulletVelocity` 14,
   1.25× multiplier). Change in `itemtypes/leveraction.json`.
5. The rifle shape is boxy (it is generated code, not hand-modelled). Open
   `shapes/firearms/leveraction.json` in the Vintage Story model editor to refine it.
6. Check the shotgun barrel hinge and rolling-block breech direction, reload timing, and .50 cartridge icon in game.

## Layout

```
source/            C# mod code
resources/assets/  Vintage Story JSON assets and textures
resources/modicon.png
```

## Troubleshooting

**`NU1100: Unable to resolve 'VSImGui (>= 0.0.6)'`** – the dependency mods require VSImGui. NuGet usually reports NU1100 when *no package source is
configured*. Check with `dotnet nuget list source`; if `nuget.org` is missing or disabled, run

    dotnet nuget add source https://api.nuget.org/v3/index.json -n nuget.org

(or `dotnet nuget enable source nuget.org`). If nuget.org is enabled and the package still isn't found, install the VSImGui mod from the mod DB and reference its `VSImGui.dll` / `ImGui.NET.dll` instead of the package in the dependency project files.

### Upgrading
Remove older `smokelessfirearms_*.zip` and legacy `smokelesslever_*.zip` files from your Mods folder before installing the new release.

### "Assembly with same name is already loaded" / mod missing from creative after an update
The game cannot unload a code mod. If you replace the zip while the game (or launcher) is still running, the old
assembly stays in memory and the new one is rejected, so the whole mod is skipped. Quit the game and launcher, replace the zip, and start fresh. Since 0.1.2 the assembly name includes the version, so a version bump can no longer
collide with an older copy in memory, but a running game still keeps running the old code until restarted.

After starting, `client-main.log` should contain `Mod 'smokelessfirearms_0.1.8.zip' (smokelessfirearms)` and
`SmokelessFirearms.SmokelessFirearmsModSystem`, and no `[Error]` lines mentioning smokelessfirearms.
