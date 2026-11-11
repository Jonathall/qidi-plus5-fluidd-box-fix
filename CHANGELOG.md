# Changelog

Bundle format: QIDI's shipped Fluidd v1.30.5 (`index-DlFvHGAh.js`).
Reference stock bundle MD5: `b9bc4faaf367d0603d92d7217476c57a`.

## V9.4 — 2026-11-11

Patched bundle MD5: `3a4a3f3123154bd0a30983a345263fd5`.
Filament table unchanged from V9.3 (SHA-256:
`4cf36a1b4aac923fc7dda4ee7e222e1c506768a6dc27156b56bdf35a0f1cb1c4`).

- **Slot colors are no longer limited to the 24-entry palette.**
  The panel's color model dated from the legacy numeric firmware:
  a color set on the printer screen reached Fluidd as a hex code,
  was converted to a palette index by exact match against
  `[colordict]`, and the tile rendered the palette entry — so any
  hex outside the table (or mistyped in it, see V9.3) collapsed to
  index 0 and disappeared. The printer itself accepts and stores
  any hex color, as does QIDI Studio. V9.4 carries the real hex
  alongside the legacy index (`variables.colorHex`, patcher
  changes 7, 10 and 11) and the three places that render a slot
  color — panel tiles, the slot item list and the external-spool
  rack — now prefer the real hex and fall back to the palette
  lookup only when no hex is known (changes 12–14). The legacy
  index resolution is unchanged, so nothing that worked before
  changes.
- **Full color picker in the color menu.** Below the 24 palette
  swatches (kept as quick presets), the menu now embeds Fluidd's
  own Iro color picker — the same component Fluidd uses for its
  LED/output colors, already shipped inside this bundle — with
  the current hex code shown under the wheel (change 15, wired
  exactly as AppColorPicker uses it: options plus a v-model
  binding on the slot's color). The component reports on release
  (`input:end`), not per drag tick, and the pick flows into the
  existing hex setter, so any color is stored on the printer
  as-is and shown back exactly. The picker and its hex readout
  sit in a wrapper whose click handler stops propagation: the
  stock menu closes on any content click, so a click in the
  wheel used to close it as the color set — now wheel and slider
  clicks never reach the menu's close handler, while swatch
  clicks keep the stock set-and-close behavior.
- **The color setter no longer drops off-palette colors.** The
  stock setter computed the picked color's palette key and the
  hex-writing tail (change 6) only ran when a key was found —
  harmless while only swatches fed it, but any other value was
  silently discarded. The key is unused by the tail, so change 16
  pins it and the write always runs. Verified on the complete
  extracted setter: before, an off-palette value produced no
  command at all; now it writes on slots 0–15 and the rack alike,
  and palette colors write exactly as before.
- Patcher grows from 10 to 16 anchored replacements; it still
  reproduces the drop-in bundle byte for byte from the reference
  stock bundle. Validated by harnesses running the patched
  bundle's own getter, tile expressions and complete color
  setter (palette hexes, the five V9.3 hexes, off-palette hexes,
  legacy numeric values, empty slots — all green). Live-tested
  on the printer 2026-11-11.

## V9.3 — 2026-11-10

Bundle unchanged (patched bundle MD5: `a0cb4b7bb1e1c63d23fb877a2fa5c`).
Filament table (`officiall_filas_list.cfg`) SHA-256:
`4cf36a1b4aac923fc7dda4ee7e222e1c506768a6dc27156b56bdf35a0f1cb1c4`

- **Color palette corrected to the hex codes the firmware writes.**
  Five `[colordict]` entries, copied verbatim from the stock table,
  did not match the hex values the printer itself stores when a
  color is set on the printer screen: #4 `#5CF30F` → `#5CF30E`,
  #7 `#FE98FE` → `#FF98FE`, #13 `#CADE4B` → `#CADF4B`,
  #17 `#FE717A` → `#FF7174`, #20 `#898F9B` → `#898F8B`. The panel
  resolves a screen-set color by exact hex match against
  `[colordict]`; on a mismatch it fell back to palette index 0 and
  the color never appeared in Fluidd. Setting a color from Fluidd
  was unaffected (Fluidd writes the hex directly and the screen
  renders it as-is), and the other 19 palette entries already
  matched. Entry #20 is verified against the author's printer,
  whose firmware publishes `color_rgb_str ['#898F8B']` for a grey
  PLA Silk slot. Correction contributed by mayrthom via a fork
  and merged here.

## Documentation — 2026-11-06

- **Documentation:** step-by-step connection and install guide
  (new *Connecting to the printer* section in the README),
  file-location warnings (READ FIRST box: exactly two files, exact
  paths and names), and an MD5 verification walkthrough. No change
  to the fix itself — V9.2 below remains the current build.

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
