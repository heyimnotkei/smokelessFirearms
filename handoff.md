# Handoff

At the start of each new chat on this project, read this file. Record code changes, attempted fixes, and the current project stage here before finishing. The user requested this convention for every project and chat. Never change model size or rotation unless explicitly asked. Keep the lever-action model unchanged; the user has confirmed it is fine.

## Current project stage

- Requested release reset: make the current AK recovery `v1.8.6`, replace the GitHub `v1.8.6` release, and delete the `v1.8.7` release/tag.
- Current source version: being reset to `1.8.6`; the replacement archive will be `Releases/smokelessfirearms_1.8.6.zip`.
- The failed `1.8.6` loaded-model merge and hand-transform changes are reverted to the pre-`1.8.6` AK state. Model sizes and rotations are unchanged.
- The Vintage Story 1.22.7 Release build succeeds with zero warnings and errors.
- No in-game check has been done for the new item-state swap.

## AK-47 history and current fix

- `1.8.4` introduced loaded and empty AK models and tried selecting the empty model through `renderVariant` in `OnHeldIdle`. The user reported it still showed the loaded model at `0/30`.
- `1.8.5` fixed the loaded model's `#missing_texture` references.
- The originally published `1.8.6` used `renderVariant` on the item shape and had broken loaded geometry/hand offsets. It did not switch the held model at zero rounds. The user requested replacing that GitHub release with the recovered build.
- Recovery restores the loaded AK model and magazine geometry to the pre-`1.8.6` file, and hand Z transforms to first-person `2` and third-person `0`. Do not change size or rotation data.
- The replacement `1.8.6` adds an internal `ak47-empty` item type with its own static `animated-shape`. The current ammo count selects the empty item at zero and the regular AK when rounds are present. ItemStack attributes are cloned on swap to retain the magazine contents and durability.
- The client updates on selection, when firing the final round, and while held. Server `Shoot` and `Reload` update the item type too, so the held shape change is authoritative and synchronized.
- No extra magazine bar was added; the existing magazine inventory count is the state source and the tooltip already displays `0/30`.

## Next step

After the release reset, install `v1.8.6` and verify in game that the AK switches to `ak47_empty` at `0/30`, returns to the loaded model after reloading, and keeps the magazine geometry intact. In-game behavior and positioning have not yet been verified. Leave lever-action files untouched; do not change model size or rotation unless asked.
