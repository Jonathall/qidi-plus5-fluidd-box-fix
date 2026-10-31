# What the patch changes, in detail

The patch is **10 anchored replacements** in the minified bundle
(`patcher/qidi_plus5_fluidd_fix.py` lists them verbatim). This document
explains what each group does and why. All of it follows one principle:
**the firmware is the source of truth** — Fluidd was adapted to the formats
and state locations the current firmware actually uses, never the other way
around.

## Background: two firmware changes the bundled Fluidd never got

1. **Filament identity migrated.** Slots used to be described by numeric
   vendor/filament/color indexes in `save_variables`. The current firmware
   identifies a filament by a **QIDI filament ID** (`QFA02`, `QFL31`,
   `QFU91`…) with a **hex color**, published per slot in
   `box_extras.boxes[].filament_info`, and for the external spool in
   `multi_color_controller.extra.filament_info` (mirrored to
   `save_variables` as `filament_slot16 = 'QFU91'`, `color_slot16 =
   ['060606']`). The vendor is *derived* from the filament ID.
2. **State relocated.** `box_extras` no longer publishes `e_endstop_state`,
   `b_endstop_state` or `box_button_state`. Their current homes:
   - external filament presence → `filament_switch_sensor
     filament_switch_sensor.filament_detected` (boolean)
   - buffer endstop → `multi_color_controller.box.b_endstop_state`
   - operation in progress → `multi_color_controller.operation.box_button_state`

Both were verified against the printer's live object state
(`/printer/objects/query`), including a field-by-field diff (697 fields) of
"external loaded" vs "external unloaded": the only state fields that track
the physical filament are `filament_detected` and
`multi_color_controller.extruder_limit_state`.

## The changes

### 1. Slot state resolution (`getVariables`) — 4 replacements

The stock code parsed the saved slot values as numbers:

```js
s[v] = parseInt(e[g] ?? "0", 10)   // parseInt("QFA02") → NaN → "?" tiles
```

Each of the three value arrays (color, filament, vendor) is now resolved
against the filament catalog: a saved QF filament ID maps to its catalog
entry (filament, vendor, color), for the box slots and for slot 16. The
fourth replacement fixes the same inconsistency in the returned rack data:
the external tile (`rackExtra`) received the raw saved values while every
other slot got the resolved ones — it now receives the resolved
`[colorSlot[16], filamentSlot[16], vendorSlot[16]]`, so the external spool
displays its actual filament, vendor and color.

### 2. Filament / vendor / color setters — 2 replacements

The stock setters wrote the legacy trio (`filament_slot<N>` = numeric index,
`color_slot<N>` = palette index, `vendor_slot<N>` = vendor index). The
firmware treats those as unset — and a legacy write to slot 16 made the
module **reset the external spool to QFA00 "PLA Basic"**.

The patched setters write what the printer screen itself writes:

- filament: `SAVE_VARIABLE VARIABLE=filament_slot<N> VALUE="'QFL31'"`
  (a quoted QF ID — Klipper parses `VALUE` as a Python literal, so the
  quotes are part of the value);
- color: `SAVE_VARIABLE VARIABLE=color_slot<N> VALUE="['DFD628']"`
  (a hex color list);
- vendor: no separate variable — changing the vendor re-points the slot to
  the same-named filament from that vendor's catalog entries, and the
  firmware derives the vendor from the ID.

This covers slots 0–15 and the external slot 16 with the same code path.
The larger of the two blocks also carries the material dropdown's vendor
scoping described in §3.

### 3. Vendor list & material filtering

One replacement builds the vendor choices from the filament catalog
actually installed on the printer. The material dropdown for a slot is
scoped to the selected vendor's filaments (falling back to the full list
if the scope is empty), instead of one mixed 56-entry list — that scoping
sits in the same component block as the setters (§2).

### 4. Print gate (`isOkPrinter`) — part of 1 replacement

Stock, with the Box disabled, the dialog required:

```js
box_extras.e_endstop_state === 1 && box_extras.b_endstop_state !== 0
```

— two fields that no longer exist, so external prints could never start
from Fluidd ("No filament detected. Please insert the external filament.").
Patched:

```js
filament_switch_sensor.filament_detected === true &&
multi_color_controller.box.b_endstop_state !== 0
```

The Box-enabled branch of the dialog (every used extruder must have a
filament assigned) reads no sensor and is unchanged.

### 5. Button state (`buttonStatus`) — 1 replacement

- **Box slots:** unchanged logic; the two reads of the removed
  `box_extras.b_endstop_state` are repointed to
  `multi_color_controller.box.b_endstop_state`. With the value the firmware
  actually publishes (1), every outcome is identical to before — this is a
  repair of a dead read, not a behavior change (verified by replaying the
  old and new logic over the full state matrix).
- **Slot 16:** the stock getter short-circuited — `selectIndex >= 16`
  skipped the whole computation and left every button disabled. The patch
  adds the missing branch, driven by `filament_detected`:
  - *Uninstall* (`E_BOX`): always disabled for the external spool;
  - *Load* (`E_LOAD slot=16`): enabled when no filament is detected;
  - *Unload* (`E_UNLOAD slot=16`): enabled when filament is loaded.

  The commands themselves are the stock handler's — `E_LOAD` / `E_UNLOAD
  SLOT=16` are the same commands the firmware's own load/unload macros
  (M604 / M603) call.

### 6. Operation lock (`isOperating`) — 1 replacement

```js
// stock
const t = printer.box_extras; return !(!t || !t.box_button_state)
// patched
const t = printer.multi_color_controller; return !(!t || !t.operation || !t.operation.box_button_state)
```

Without this, the panel never locked during a load/unload: every button,
dropdown and RFID action stayed live, and starting a print mid-load crashed
Klipper (`Macro G28 called recursively` — both flows home the printer).

### 7. Vendor-switch fallback — part of 1 replacement (V9.2)

The vendor setter (§2) remaps the slot's material when the vendor changes:
same material name in the new vendor first, then same type. Both can miss —
the catalog's exotic types (ASA, TPU variants, PLA-CF) exist only under
QIDI, so switching such a material to Bambu Lab, HATCHBOX, Overture or
Polymaker matched nothing, and the setter wrote nothing at all. With no
state change, the material dropdown (§3) kept filtering on the old vendor
and never refreshed. The setter now falls back to the new vendor's first
catalog filament, so every vendor switch writes a valid QF ID and the list
follows. Verified exhaustively over the shipped catalog: all 280 possible
vendor switches now produce a write, and every switch that already worked
produces the same ID as before.

## The filament table

`officiall_filas_list.cfg` is not generated by the patcher; it is the QIDI
Studio v2.07.02.73 filament catalog (56 filaments, 6 vendors) transcribed
into the format Fluidd reads on the printer, each entry carrying its
`filament_id`. Fluidd resolves everything — display, editing, the dialog's
slot mapping — through this table, so it is required with both install
paths.
