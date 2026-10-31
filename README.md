# QIDI Plus 5 — Fluidd Box & External Spool Fix

A patch for the Fluidd web interface bundled with the **QIDI Plus 5**, so the
Control Box panel, the external spool and the print dialog work again with the
current firmware.

> **Status.** Field-tested on the author's printer (filament read/write
> between Fluidd and the printer screen, box slots and external spool).
> Current build: V9.2.

## The problem

After a 2026 firmware update, QIDI's firmware stores each slot's filament as a
**QIDI filament ID** (e.g. `QFA02`) plus a **hex color**, and keeps the box
state in `multi_color_controller`. The Fluidd build QIDI ships (v1.30.5) was
never updated for that change, so in the web interface:

- every box slot shows "**?**" instead of its filament;
- editing a slot's vendor / filament / color writes legacy values the firmware
  treats as "not set" — worse, it can **reset the external spool** to
  "PLA Basic";
- the external spool (slot 16) can't be managed from Fluidd at all;
- with the Box disabled, starting a print from Fluidd is impossible: the print
  dialog always claims *"No filament detected. Please insert the external
  filament."* even with filament loaded — it reads sensor fields the firmware
  no longer publishes;
- the Load / Unload buttons for the external spool are permanently greyed out.

This patch repairs the bundled Fluidd in place — no replacement UI, nothing
to run on your PC.

## Compatibility

- **Printer:** QIDI Plus 5 with a QIDI Box (developed and tested with one Box).
- **Fluidd:** v1.30.5, bundle `assets/index-DlFvHGAh.js`.
- **The real compatibility check is the bundle itself.** Reference stock
  bundle: 1,778,604 bytes, MD5 `b9bc4faaf367d0603d92d7217476c57a`.
  The patcher script verifies this before touching anything (see below).
- Not for the Max4 or Q2 — different printers, different bundles; do not
  cross-apply.

## What you need

Two files, **both are required**, whichever install path you choose:

| File | Goes to | Role |
| --- | --- | --- |
| `index-DlFvHGAh.js` (patched bundle) | `~/fluidd/assets/` on the printer | the repaired interface |
| `officiall_filas_list.cfg` | `~/printer_data/config/` on the printer | filament catalog in the new format: 56 filaments from the QIDI Studio catalog (Generic, QIDI, HATCHBOX, Polymaker, Bambu Lab, Overture) with their filament IDs |

Access to the printer's files is via SFTP (the printer's `qidi` account, same
as QIDI's documentation describes), e.g. with WinSCP or FileZilla, to the
printer's IP address.

## Install — path A: drop-in files (simplest)

1. **Check your stock bundle first.** Download `index-DlFvHGAh.js` from
   `~/fluidd/assets/` and verify its MD5 is
   `b9bc4faaf367d0603d92d7217476c57a`. If it does not match, **stop** — your
   Fluidd build differs; use path B so the anchors can verify your build, or
   don't apply the fix.
2. **Back up.** On the printer, rename the original bundle to
   `index-DlFvHGAh.js.orig`, and `officiall_filas_list.cfg` in
   `~/printer_data/config/` to `officiall_filas_list.cfg.orig`.
3. **Upload** the two files from this repo's `drop-in/` folder to the
   locations in the table above (the bundle must be named exactly
   `index-DlFvHGAh.js`).
4. **Hard-refresh** Fluidd in your browser (Ctrl+F5).

## Install — path B: patcher script (verifiable)

`patcher/qidi_plus5_fluidd_fix.py` applies the same fix as 10 anchored
replacements — each anchor must be found exactly once in your bundle or the
script refuses to modify anything. On the reference stock bundle it produces
the drop-in file **byte for byte** (MD5 `4eefc7febb88db296a2c9a7d30fb4031`).

```sh
# on your PC, against a downloaded copy of your bundle:
python3 qidi_plus5_fluidd_fix.py --check    index-DlFvHGAh.js   # verify, change nothing
python3 qidi_plus5_fluidd_fix.py --dry-run  index-DlFvHGAh.js   # simulate
python3 qidi_plus5_fluidd_fix.py            index-DlFvHGAh.js   # apply (writes index-DlFvHGAh.js.orig backup)
python3 qidi_plus5_fluidd_fix.py --restore  index-DlFvHGAh.js   # undo from the backup
```

Then upload the patched bundle **and** the filament table
(`drop-in/officiall_filas_list.cfg`) as in path A, steps 2–4. The script can
also run directly on the printer over SSH, in `~/fluidd/assets/`.

If your bundle is not the reference stock build, the script stops. With
`--force` it will still patch **if** all 10 anchors match your build exactly;
the result will differ from the reference patched bundle and is untested —
you proceed at your own risk.

## What the fix does

- **Identity read/write (box slots).** Slots are read from the firmware's own
  filament data and written back as filament IDs + hex colors — the formats
  the firmware and the printer screen use. What you set in Fluidd is what the
  screen shows, and vice versa.
- **External spool (slot 16) end to end.** Same treatment for the external
  spool: read, set filament/color, no more resets to "PLA Basic".
- **Vendor filtering.** The material dropdown is filtered by the selected
  vendor (with a fallback to the full list), instead of one long mixed list.
- **Print gate repaired.** The print dialog (Box disabled) now reads filament
  presence from `filament_switch_sensor`, where the current firmware actually
  publishes it, instead of the removed `box_extras` fields. External prints
  can start from Fluidd again.
- **Contextual Load / Unload buttons.** The external slot gains a real button
  logic (it had none — its buttons were greyed out by construction): Load is
  enabled when no filament is detected, Unload when filament is loaded.
  *Uninstall* stays disabled for the external spool. Box-slot buttons keep
  their original logic, with one dead state read repointed.
- **Operation lock.** The panel once again locks its buttons and dropdowns
  while a load/unload operation is running (it read a state field the
  firmware no longer publishes, so it never locked).

Details, change by change: [docs/changes.md](docs/changes.md).

## Known limitations

- **QIDI Studio** still cannot start external-spool prints (a separate,
  PC-side issue, widely reported since Studio 2.07.02.73). That is QIDI's to
  fix; printing from Fluidd or the printer screen works.
- **One operation at a time.** Do not start a print while a load/unload is
  still running — the print dialog cannot see module operations, and stacking
  the two crashed Klipper in testing ("Macro G28 called recursively").
  Let load/unload finish first.
- **Vendor follows the filament.** By design — that is how the firmware
  models it. You pick the filament; its vendor comes with it.
- **RFID:** written for manual filament assignment; RFID flows are untouched
  and untested.
- **Multi-Box** (2+ Boxes / RS485): untested.
- **Firmware updates overwrite the bundle.** After any QIDI firmware update,
  reapply the fix (the patcher will refuse if the new bundle build is
  unsupported).

## Uninstall

Restore the two `.orig` backups over the patched files and hard-refresh
(Ctrl+F5). Nothing else on the printer is modified.

## Acknowledgement

The *packaging* of this repo — a ready-to-install drop-in file plus a
verifiable, anchored patch script — was inspired by
[Assur92's Max4 Fluidd fix](https://github.com/Assur92/qidi-max4-fluidd-box-fix).
The Plus 5 fix itself was developed independently, from the printer's own
live state and firmware data.

## License

GPL-3.0 — see [LICENSE](LICENSE). Fluidd and QIDI's Klipper/Moonraker
editions are GPL-3.0; this patch is distributed under the same terms.
