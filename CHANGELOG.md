# Changelog

Bundle format: QIDI's shipped Fluidd v1.30.5 (`index-DlFvHGAh.js`).
Reference stock bundle MD5: `b9bc4faaf367d0603d92d7217476c57a`.

## V9.2 — 2026-10-30

Patched bundle MD5: `a0cb4b7bb1e1c63d23fb877a2fa5ba5c`

- **Material list now refreshes on every vendor switch.** Switching a slot's
  vendor remaps the current material by name, then by type. When the new
  vendor carried neither (142 of the 280 possible switches in the shipped
  catalog — e.g. QIDI ASA or TPU toward Bambu Lab, HATCHBOX, Overture or
  Polymaker), the setter wrote nothing: the slot state never changed, so the
  material dropdown kept showing the previous vendor's list. It now falls
  back to the new vendor's first catalog filament, so a vendor switch always
  lands on a valid material and the list refreshes.

## V9.1 — 2026-10-30

Patched bundle MD5: `4eefc7febb88db296a2c9a7d30fb4031`

- **Operation lock restored.** The panel's "operation in progress" state was
  read from `box_extras.box_button_state`, which the current firmware no
  longer publishes — so buttons and dropdowns never locked during a
  load/unload, and stacking a second action crashed Klipper with
  *"Macro G28 called recursively"* (observed on the author's printer).
  The state now comes from `multi_color_controller.operation`, where the
  firmware publishes it.

## V9 — 2026-10-30

- **Print gate repaired.** The print dialog required
  `box_extras.e_endstop_state === 1` and `box_extras.b_endstop_state !== 0`
  to start an external print; the firmware publishes neither field anymore,
  so the gate could never pass. Presence is now read from
  `filament_switch_sensor.filament_detected` (verified to track the physical
  external filament on the author's machine), and the buffer state from
  `multi_color_controller.box.b_endstop_state`. The Box-enabled branch of
  the dialog is unchanged.
- **External Load / Unload buttons.** The button-state logic had no branch
  for slot 16 at all — its buttons were greyed out by construction. It now
  follows `filament_detected`: Load enabled when no filament is detected,
  Unload enabled when filament is loaded. *Uninstall* stays disabled for
  the external spool. Box slots keep their original logic, with the same
  relocated `b_endstop_state` read repointed (behavior proven unchanged).

## V8 — 2026-10-30

- **External spool write fixed end to end.** The external slot was still
  written in the legacy format, which made the firmware module reset it to
  "QFA00 PLA Basic". It is now written as a filament ID + a hex color list,
  like the box slots, and the rack display resolves the same way.
- **Vendor handling for the external slot** follows the filament (vendor is
  derived from the filament ID), matching the printer screen.
- **Material dropdown filtered by vendor** (full-list fallback when the
  filtered list would be empty).

## V7 — 2026-10-23

- **Slot identity read/write in the firmware's native format.** The bundled
  Fluidd parsed slot values as legacy numbers (`parseInt("QFA02")` → NaN,
  hence the "?" tiles) and wrote numeric codes back. Slots are now resolved
  and written through the filament catalog (`officiall_filas_list.cfg`,
  56 filaments with QIDI filament IDs): filament as a quoted QF ID, color as
  a hex list — exactly what the firmware and the printer screen use.
- The external slot is included in the slot state (slot 16) instead of being
  dropped.
