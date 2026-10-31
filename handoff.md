# Handoff

At the start of each new chat on this project, read this file. Record code changes, attempted fixes, and the current project stage here before finishing. The user requested this convention for every project and chat. Never change model size or rotation unless explicitly asked. Keep the lever-action model unchanged; the user has confirmed it is fine.

## Current project stage

- Latest published release: replacement `v1.8.6`; the prior `v1.8.6` and `v1.8.7` releases/tags were deleted. The replacement archive is `Releases/smokelessfirearms_1.8.6.zip`.
- Branch: `main`; recovery source commit `47c96b3` is pushed and tagged `v1.8.6`.
- Current changes fix ammo getting stuck at `1/30` and adjust the AK position. The user has now authorized build, commit, push, and release while keeping version `1.8.6`.
- The AK hand position was shifted along transform X instead of the previously tried Z direction. User found the first offset too far forward, so it has been halved: first-person X is now `-0.4` (from `0.2`), third-person X is `-0.6` (from `0`), moving another `0.1` in the established forward direction. Needs in-game confirmation. Size and rotation are unchanged.
- The Vintage Story 1.22.7 Release build succeeds with zero warnings and errors.
- No in-game check has been done for the new item-state swap.

## AK-47 history and current fix

- `1.8.4` introduced loaded and empty AK models and tried selecting the empty model through `renderVariant` in `OnHeldIdle`. The user reported it still showed the loaded model at `0/30`.
- `1.8.5` fixed the loaded model's `#missing_texture` references.
- The originally published `1.8.6` used `renderVariant` on the item shape and had broken loaded geometry/hand offsets. It did not switch the held model at zero rounds. The user requested replacing that GitHub release with the recovered build.
- Recovery restores the loaded AK model and magazine geometry to the pre-`1.8.6` file, and hand Z transforms to first-person `2` and third-person `0`. Do not change size or rotation data.
- The replacement `1.8.6` adds an internal `ak47-empty` item type with its own static `animated-shape`. ItemStack attributes are cloned on swap to retain the magazine contents and durability.
- The first 1.8.6 implementation predicted a zero-ammo item swap on the client before sending the shot packet. The packet carries the current item ID; the server still had the loaded AK ID, rejected the shot, and synchronized the stack back at `1/30`. This explains the brief empty-model flash and stuck round.
- Current uncommitted fix makes model swaps server-authoritative: after a successful shot/reload, plus the server-held idle fallback. It removes the pre-shot and client-held swaps so the packet uses the matching item ID.
- No extra magazine bar was added; the existing magazine inventory count is the state source and the tooltip already displays `0/30`.

## Next step

Build, commit, push, and replace the GitHub `v1.8.6` release with the current archive. Then verify in game that shots consume ammo through `0/30`, the empty model stays after the last shot, reloading restores the loaded model, and the gun position is correct. Leave lever-action files untouched; do not change model size or rotation.
