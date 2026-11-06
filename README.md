# QIDI Plus 5 — Fluidd Box & External Spool Fix

A patch for the Fluidd web interface bundled with the **QIDI Plus 5**, so the
Control Box panel, the external spool and the print dialog work again with the
current firmware.

> **Status.** Field-tested on the author's printer (filament read/write
> between Fluidd and the printer screen, box slots and external spool).
> Current build: V9.2.

## ⚠️ READ FIRST — Where the files go

**This fix replaces exactly TWO files. Everything else on the
printer stays exactly as it is.** Most failed installs of patches
like this one are a file copied to the wrong place — read this
before copying anything.

- ✅ **The bundle goes here, and only here:**
  `/home/qidi/fluidd/assets/index-DlFvHGAh.js`
  Verify the file already there by MD5 **before** replacing it
  (it must be the stock MD5 in *Compatibility* below), and verify
  again **after** (it must be the patched MD5 — see *Verify the
  install*).
- 🚫 **Do not touch any other `index-*.js`.** Other bundle files
  can sit in `/home/qidi/fluidd/assets/`. Exactly one file
  matters: the one named precisely **`index-DlFvHGAh.js`**. Leave
  every other file in that folder alone.
- ✅ **The filament catalog goes here, and only here:**
  `/home/qidi/printer_data/config/officiall_filas_list.cfg`

- 🔄 **Last step, do not skip it: hard-refresh Fluidd** in your
  browser (**Ctrl+F5**, or **Cmd+Shift+R** on Mac). Fluidd's
  service worker can keep serving the old bundle from your
  browser's cache — a perfectly correct install can look
  completely unchanged until you hard-refresh.

Two files, two exact locations, exact names. If a step below
seems to say otherwise, this box wins.

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
| `index-DlFvHGAh.js` (patched bundle) | `/home/qidi/fluidd/assets/` on the printer | the repaired interface |
| `officiall_filas_list.cfg` | `/home/qidi/printer_data/config/` on the printer | filament catalog in the new format: 56 filaments from the QIDI Studio catalog (Generic, QIDI, HATCHBOX, Polymaker, Bambu Lab, Overture) with their filament IDs |

You move these files with an SFTP program from your computer.
If you have never done that, the next section —
*Connecting to the printer* — walks through it click by click;
the install paths after it refer back to its steps.

## Connecting to the printer

You will connect to the printer from your computer with a
file-transfer program and copy two files onto it. Nothing here
can damage the printer: until the install paths tell you to
upload, you are only looking.

**Before you start**

- A computer on the **same network** as the printer — the same
  home Wi-Fi, or plugged into the same router.
- The printer **switched on and idle**: no print running, no
  filament load/unload in progress.
- About 15–20 minutes.
- The two files from this repo's `drop-in/` folder, saved
  somewhere you can find them again (for example your Downloads
  folder). If you downloaded this repo as a ZIP, unzip it first.

**Step 1 — Find the printer's IP address**

On the printer's touchscreen, open the settings page that shows
the network / Wi-Fi status: the printer's IP address is displayed
there. Write it down. It looks like four numbers separated by
dots — typically `192.168.1.` followed by one more number.

Alternative: log in to your router's administration page and look
at its list of connected devices; the printer appears there with
its address.

**Step 2 — Install a file-transfer program**

The printer accepts file transfers over **SFTP** — copying files
through SSH, on port 22. A free program handles it:

- **Windows:** WinSCP, from
  [winscp.net](https://winscp.net). Download it and install it
  with the default options. The steps below are written for
  WinSCP.
- **Mac:** Cyberduck, from [cyberduck.io](https://cyberduck.io).
  The fields to fill in are the same as in step 3; only the
  window layout differs.
- FileZilla ([filezilla-project.org](https://filezilla-project.org))
  also works, on both.

Such a program shows two panels side by side: your computer's
files on the left, the printer's files on the right. You copy a
file by dragging it from one side to the other.

**Step 3 — Log in to the printer**

Open WinSCP. A **Login** window appears, with a session form.
Fill it in:

| Field | Value |
| --- | --- |
| File protocol | `SFTP` |
| Host name | the printer's IP address (step 1) |
| Port number | `22` |
| User name | `qidi` |
| Password | `qiditech` |

Click **Login**.

The first time, a warning appears saying the server's host key
is unknown (wording like *"The server's host key was not found
in the cache"* or *"Potential security breach"*). This is
**normal on a first connection**: your computer has simply never
met this printer before. Check that the address in the warning
is the IP address from step 1, then click **Yes** to accept the
key and continue.

> **About the login.** `qidi` / `qiditech` are the Plus 5's
> factory-default SSH credentials, as QIDI's documentation
> describes — the same on every Plus 5. If you have changed the
> password on your printer, use yours instead. These credentials
> give full access to the printer's files, so keep your printer
> on your own network.

You are in when the two panels appear: left = your computer,
right = the printer, starting in the `qidi` home folder
(`/home/qidi`).

(In Cyberduck: click **Open Connection**, choose **SFTP (SSH
File Transfer Protocol)** as the protocol, then the same server
= IP, port 22, username and password. An "unknown fingerprint"
prompt on first connection is the same host-key warning —
verify the IP and click **Allow** / **Continue**.)

**Step 4 — Go to the two folders (and only these two)**

Each panel has a path field above it showing the folder it is
currently displaying. On the **right** (printer) panel, click in
that path field, type the exact path, and press Enter.

You will only ever need these two folders on the printer:

- `/home/qidi/fluidd/assets` — holds the bundle file;
- `/home/qidi/printer_data/config` — holds the filament catalog.

That is the whole geography of this fix — the same two locations
as in the ⚠️ box at the top. Do not wander elsewhere on the
printer's disk; nothing else needs you.

**Step 5 — Back up a file (do this before every replacement)**

Never replace a file on the printer without keeping the original
under a backup name **in the same folder**. Here, backups are
made by *renaming* the original by adding `.orig` to its name.
Do it for **both** files before uploading anything. Two ways —
pick one:

*Graphical (WinSCP):*

1. In the right panel, go to the file's folder (step 4).
2. Right-click the file → **Rename**.
3. Add `.orig` at the very end of the name — for example
   `index-DlFvHGAh.js` becomes `index-DlFvHGAh.js.orig` — and
   confirm (Enter / **OK**).
4. The original now sits next to where it was, under its backup
   name, and the original name is free for the new file.

(In Cyberduck: right-click the file → **Info** / **Rename**,
and edit the name the same way.)

*Terminal (still inside WinSCP):*

1. Menu **Commands → Open Terminal** (a black console window
   opens, connected to the printer).
2. Type each line below and press Enter after each. No message
   back means success.

```sh
mv /home/qidi/fluidd/assets/index-DlFvHGAh.js /home/qidi/fluidd/assets/index-DlFvHGAh.js.orig
mv /home/qidi/printer_data/config/officiall_filas_list.cfg /home/qidi/printer_data/config/officiall_filas_list.cfg.orig
```

3. Close the terminal window when done.

**Step 6 — Upload a file (the procedure the install paths use)**

1. In the **left** panel, go to the folder on your computer
   where the new file is (path field above the left panel, same
   as step 4).
2. **Check the file's name character by character.** Web
   browsers sometimes rename a downloaded file by adding a
   suffix like ` (1)`. If the name is not *exactly* the required
   one, right-click it → **Rename** and fix it **before**
   uploading. A file with the wrong name is simply ignored by
   the printer.
3. Drag the file from the left panel onto the right panel. A
   copy dialog appears — confirm it (**OK** / **Upload**).
4. If an overwrite confirmation appears (because a file with
   that name is still on the printer), click **Yes**.
5. Wait until the transfer finishes (progress bar completes, no
   error message). The file on the right panel now shows today's
   date and the new size.

### Command-line alternative (ssh / scp)

If you are comfortable in a terminal, the same work without the
graphical program (first connection asks you to confirm the
printer's fingerprint — type `yes`; the password asked for is
`qiditech`):

```sh
IP=192.168.1.XXX   # the printer's IP address (step 1)

# 1. Back up both files on the printer (rename to .orig)
ssh qidi@$IP 'mv /home/qidi/fluidd/assets/index-DlFvHGAh.js /home/qidi/fluidd/assets/index-DlFvHGAh.js.orig'
ssh qidi@$IP 'mv /home/qidi/printer_data/config/officiall_filas_list.cfg /home/qidi/printer_data/config/officiall_filas_list.cfg.orig'

# 2. Upload the two files, exact names, exact places
scp drop-in/index-DlFvHGAh.js        qidi@$IP:/home/qidi/fluidd/assets/index-DlFvHGAh.js
scp drop-in/officiall_filas_list.cfg qidi@$IP:/home/qidi/printer_data/config/officiall_filas_list.cfg

# 3. Check what is actually on the printer now
ssh qidi@$IP 'md5sum /home/qidi/fluidd/assets/index-DlFvHGAh.js'
```

## Install — path A: drop-in files (simplest)

1. **Connect to the printer** — follow *Connecting to the
   printer*, steps 1–3.
2. **Check your stock bundle first.** In the right panel, go to
   `/home/qidi/fluidd/assets` (step 4 of *Connecting*) and
   download `index-DlFvHGAh.js` to your computer (drag it from
   the right panel to the left). Verify its MD5 is
   `b9bc4faaf367d0603d92d7217476c57a`. To compute an MD5 on your
   computer: Windows — open a command prompt in the file's
   folder and run `certutil -hashfile index-DlFvHGAh.js MD5`;
   Mac — `md5 index-DlFvHGAh.js`; Linux — `md5sum
   index-DlFvHGAh.js`. If it does not match, **stop** — your
   Fluidd build differs; use path B so the anchors can verify
   your build, or don't apply the fix.
3. **Back up both files** — follow step 5 of *Connecting* for
   the bundle (`index-DlFvHGAh.js` → `index-DlFvHGAh.js.orig`)
   and for the catalog (`officiall_filas_list.cfg` →
   `officiall_filas_list.cfg.orig`, in
   `/home/qidi/printer_data/config`).
4. **Upload the bundle** — follow step 6 of *Connecting*: into
   `/home/qidi/fluidd/assets`, under the exact name
   `index-DlFvHGAh.js`, and nowhere else.
5. **Upload the filament catalog** — in the right panel, go to
   `/home/qidi/printer_data/config` (step 4 of *Connecting*),
   then upload as in step 6: `officiall_filas_list.cfg` from
   this repo's `drop-in/` folder, exact name, into that folder
   only. (The original is already renamed to
   `officiall_filas_list.cfg.orig` from step 3 above.)
6. **Hard-refresh** Fluidd in your browser (Ctrl+F5).
7. **Verify the install** (next section) — do not skip this.

## Install — path B: patcher script (verifiable)

`patcher/qidi_plus5_fluidd_fix.py` applies the same fix as 10 anchored
replacements — each anchor must be found exactly once in your bundle or the
script refuses to modify anything. On the reference stock bundle it produces
the drop-in file **byte for byte** (MD5 `a0cb4b7bb1e1c63d23fb877a2fa5ba5c`).

```sh
# on your PC, against a downloaded copy of your bundle:
python3 qidi_plus5_fluidd_fix.py --check    index-DlFvHGAh.js   # verify, change nothing
python3 qidi_plus5_fluidd_fix.py --dry-run  index-DlFvHGAh.js   # simulate
python3 qidi_plus5_fluidd_fix.py            index-DlFvHGAh.js   # apply (writes index-DlFvHGAh.js.orig backup)
python3 qidi_plus5_fluidd_fix.py --restore  index-DlFvHGAh.js   # undo from the backup
```

Then connect to the printer (*Connecting to the printer*,
steps 1–4) and upload the patched bundle **and** the filament
table (`drop-in/officiall_filas_list.cfg`) as in path A,
steps 3–6 — back both originals up as `.orig` first, then
upload each file to its exact location. The script can also
run directly on the printer over SSH, in `~/fluidd/assets/`.

If your bundle is not the reference stock build, the script stops. With
`--force` it will still patch **if** all 10 anchors match your build exactly;
the result will differ from the reference patched bundle and is untested —
you proceed at your own risk.

## Verify the install

1. **Re-download the served file.** Fetch
   `/home/qidi/fluidd/assets/index-DlFvHGAh.js` from the printer
   again (right panel → drag it back to your computer) and
   check its MD5 — with the same command as in path A, step 2
   (`certutil -hashfile … MD5` on Windows, `md5 …` on Mac,
   `md5sum …` on Linux). It must now be
   `a0cb4b7bb1e1c63d23fb877a2fa5ba5c` (the patched bundle). If
   you still see the stock MD5
   `b9bc4faaf367d0603d92d7217476c57a`, the new file did not land
   in the served location — re-check the ⚠️ box at the top.
2. **Hard-refresh** Fluidd in your browser (**Ctrl+F5**).
   Fluidd ships a service worker that can keep serving the
   previous bundle from cache; a verified install can look
   unchanged until you do this.
3. **Look at the Control Box panel.** Slots that hold filament
   now show a filament name instead of "**?**", and the
   external spool can be managed from the panel.

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
