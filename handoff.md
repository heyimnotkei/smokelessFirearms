# Handoff

At the start of each new chat on this project, read this file. Record code changes, attempted fixes, and the current project stage here before finishing. The user requested this convention for every project and chat. Keep the lever-action model unchanged; the user has confirmed it is fine.

## Current project stage

- Latest published release: `v1.8.6`.
- Branch: `main`, synced with `origin/main`.
- AK fix commit: `7126ea0` (`Fix AK empty model and hand position`), pushed and published as `v1.8.6`.
- The Vintage Story 1.22.7 Release build succeeds with zero warnings and errors.
- No in-game check has been done for the new empty-model switching or forward hand position.

## AK-47 history and current fix

- `1.8.4` introduced loaded and empty AK models and tried selecting the empty model through `renderVariant` in `OnHeldIdle`. The user reported it still showed the loaded model at `0/30`.
- `1.8.5` fixed the loaded model's `#missing_texture` references.
- `1.8.6` sets `renderVariant` on selection, immediately before firing the last round, during server reload, and while held. The item shape's alternate remains `ak47_empty`.
- The loaded model is assembled from the empty model's 22 shared elements plus the loaded model's three magazine elements. This copies all shared bounds, pivots, and rotations from the empty model.
- `fpHandTransform.translation.z` and `tpHandTransform.translation.z` each moved forward by one unit.

## Next step

Install release `v1.8.6` and verify in game that the AK switches to the magazine-free model at `0/30` and sits farther forward. If shape switching still fails, trace CombatOverhaul's `AnimatableAttachable` held render path: the earlier item-shape `renderVariant` approach did not meet the user's in-game requirement.
