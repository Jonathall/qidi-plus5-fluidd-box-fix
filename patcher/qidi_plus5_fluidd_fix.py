#!/usr/bin/env python3
"""
QIDI Plus 5 - Fluidd Box & External Spool Fix - bundle patcher

Patches the stock Fluidd bundle shipped on the QIDI Plus 5
(assets/index-DlFvHGAh.js, Fluidd v1.30.5) so the Control Box panel,
the external spool (slot 16) and the print dialog work with the current
firmware, which identifies filaments by QIDI filament IDs (QFA00, QFL31...)
and hex colors instead of the legacy numeric format the bundled Fluidd
still expects.

The patch is a set of 10 anchored replacements (each anchor must be found
exactly once, or the script refuses to touch the file). On the reference
stock bundle it reproduces the tested patched bundle byte for byte.

Usage:
  python3 qidi_plus5_fluidd_fix.py [path/to/index-DlFvHGAh.js]           apply (keeps a .orig backup)
  python3 qidi_plus5_fluidd_fix.py --check    [path]                     verify only, change nothing
  python3 qidi_plus5_fluidd_fix.py --dry-run  [path]                     simulate, change nothing
  python3 qidi_plus5_fluidd_fix.py --restore  [path]                     restore the .orig backup
  python3 qidi_plus5_fluidd_fix.py --force    [path]                     apply even if the bundle is
                                                                         not the reference stock build
                                                                         (anchors are still verified)

Default path: ./index-DlFvHGAh.js if present, else ~/fluidd/assets/index-DlFvHGAh.js
(run it on your PC against a downloaded copy, or on the printer over SSH).

IMPORTANT: the bundle is only half of the fix. The filament table
officiall_filas_list.cfg (see the drop-in folder) must also be installed
in ~/printer_data/config/ on the printer. See README.md.

License: GPL-3.0 (Fluidd and QIDI's Klipper/Moonraker editions are GPL-3.0;
this patch is distributed under the same terms).
"""
import hashlib
import os
import shutil
import sys

STOCK_MD5 = "b9bc4faaf367d0603d92d7217476c57a"    # reference stock bundle (Fluidd v1.30.5, Plus 5)
PATCHED_MD5 = "a0cb4b7bb1e1c63d23fb877a2fa5ba5c"  # expected result on the reference stock bundle

PATCHES = [
    # --- change 1 ---
    ('get isOkPrinter(){return this.enableBox===!1?this.$store.state.printer.printer.box_extras.e_endstop_state===1?this.$store.state.printer.printer.box_extras.b_endstop_state===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot[t]))}',
     'get isOkPrinter(){return this.enableBox===!1?((this.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"]||{}).filament_detected===!0)?(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot[t]))}'),
    # --- change 2 ---
    ('for(const s in this.officialFilasListDictData)s.startsWith("fila")&&t.add(this.officialFilasListDictData[s].filament);',
     'const cv=this.items&&this.items[this.selectIndex]?this.items[this.selectIndex].vendor:null;for(const s in this.officialFilasListDictData){if(!s.startsWith("fila"))continue;const e=this.officialFilasListDictData[s];if(cv&&e.vendor!==cv)continue;t.add(e.filament)}if(t.size===0)for(const s in this.officialFilasListDictData)s.startsWith("fila")&&t.add(this.officialFilasListDictData[s].filament);'),
    # --- change 3 ---
    ('get isOperating(){const t=this.$store.state.printer.printer.box_extras;return!(!t||!t.box_button_state)}',
     'get isOperating(){const t=this.$store.state.printer.printer.multi_color_controller;return!(!t||!t.operation||!t.operation.box_button_state)}'),
    # --- change 4 ---
    ('return this.selectIndex>=16||(this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0),t}',
     'if(this.selectIndex>=16){const D=(this.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"]||{}).filament_detected===!0;t[1]=D,t[2]=!D}else this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0;return t}'),
    # --- change 5 ---
    ('s&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot16 VALUE="${s}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${s}"`))}get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot16 VALUE="${s.replace("fila","")}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${s.replace("fila","")}"`))}',
     'const cur=(this.items||[])[this.selectIndex]||{},nm=cur.filament;let hit=null,typ=null;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(!e||!e.filament_id)continue;if(e.vendor===t&&e.filament===nm)hit=e;if(e.vendor===cur.vendor&&e.filament===nm)typ=e.type}if(!hit&&typ){for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.vendor===t&&e.type===typ){hit=e;break}}}if(!hit){for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.vendor===t){hit=e;break}}}if(hit)I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="\'${hit.filament_id}\'"`)}\nget selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){let q=null;const cv=((this.items||[])[this.selectIndex]||{}).vendor;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.filament===t&&e.vendor===cv){q=e.filament_id;break}}if(!q)for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.filament===t){q=e.filament_id;break}}const bx=(this.$store.state.printer.printer.box_extras||{}).boxes||[];if(!q)for(const b of bx){const fis=(b&&b.filament_info)||[];for(const fi of fis)if(fi&&fi.filament_str===t&&fi.filament_id){q=fi.filament_id;break}if(q)break}if(!q){const ex=((this.$store.state.printer.printer.multi_color_controller||{}).extra||{}).filament_info;if(ex&&ex.filament_str===t&&ex.filament_id)q=ex.filament_id}let w=null;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.vendor&&e.filament===t){w=this.getKeyByValue(this.officialFilasListDictData.vendor_list,e.vendor);break}}for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot16 VALUE="${q?"\'"+q+"\'":"\'"+(this.officialFilasListDictData[s].filament_id||s.replace("fila",""))+"\'"}"`):(I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${q?"\'"+q+"\'":s.replace("fila","")}"`), w&&I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${w}"`)))}'),
    # --- change 6 ---
    ('s&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot16 VALUE="${s}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="${s}"`))}',
     's&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot16 VALUE="[\'${String(t).replace("#","")}\']"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="[\'${String(t).replace("#","")}\']"`))}'),
    # --- change 7 ---
    ('s[v]=parseInt(e[g]??"0",10)}',
     'const V=e[g];let hx=null;if(Array.isArray(V))hx="#"+V[0];else if(typeof V==="string"&&V.charAt(0)==="[")hx="#"+V.replace(/[\\[\\]\'"\\s]/g,"");if(hx!==null){const cd=((r.officiallFilasList||{}).colordict)||{},fk=Object.keys(cd).find(k=>String(cd[k]).toUpperCase()===hx.toUpperCase());s[v]=fk?parseInt(fk,10):0}else s[v]=parseInt(V??"0",10)}'),
    # --- change 8 ---
    ('n[v]=parseInt(e[g]??"0",10)}',
     'const V=e[g];if(typeof V==="string"&&isNaN(parseInt(V,10))){const cat=r.officiallFilasList||{},dk=Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament_id===V);if(dk)n[v]=parseInt(dk.replace("fila",""),10);else{const bx=(r.printer.box_extras||{}).boxes||[];let nm=null;for(const b of bx){const fis=(b&&b.filament_info)||[];for(const fi of fis)if(fi&&fi.filament_id===V){nm=fi.filament_str;break}if(nm)break}if(!nm){const bz=bx[Math.floor(v/4)],fi=bz&&bz.filament_info?bz.filament_info[v%4]:null;nm=fi?fi.filament_str:null}const fk=nm?Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament===nm):null;n[v]=fk?parseInt(fk.replace("fila",""),10):0}}else n[v]=parseInt(V??"0",10)}'),
    # --- change 9 ---
    ('i[v]=parseInt(e[g]??"0",10)}',
     'const FV=e["filament_slot"+v];if(typeof FV==="string"&&isNaN(parseInt(FV,10))){const cat=r.officiallFilasList||{},vl=cat.vendor_list||{},bx=(r.printer.box_extras||{}).boxes||[],bz=bx[Math.floor(v/4)],fi=bz&&bz.filament_info?bz.filament_info[v%4]:null,vs=fi?fi.vendor_str:null,fk=vs?Object.keys(vl).find(k=>vl[k]===vs):(()=>{const dk=Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament_id===FV),ev=dk?cat[dk].vendor:null;return ev?Object.keys(vl).find(k=>vl[k]===ev):null})();i[v]=fk?parseInt(fk,10):parseInt(e[g]??"0",10)}else i[v]=parseInt(e[g]??"0",10)}'),
    # --- change 10 ---
    ('return a[16]=1,{boxCount:t,colorSlot:s,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:c,lastLoadSlot:u}',
     'return a[16]=1,{boxCount:t,colorSlot:s,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:[s[16],n[16],i[16]],lastLoadSlot:u}'),
]


def md5_of(data):
    return hashlib.md5(data).hexdigest()


def find_default_path():
    for cand in ("index-DlFvHGAh.js",
                 os.path.expanduser("~/fluidd/assets/index-DlFvHGAh.js")):
        if os.path.exists(cand):
            return cand
    return None


def apply_patches(text):
    """Apply every anchored replacement; return patched text or raise."""
    for i, (old, new) in enumerate(PATCHES, 1):
        n = text.count(old)
        if n != 1:
            raise RuntimeError(f"change {i}: anchor found {n} times (expected 1) - "
                               "this bundle build is not supported")
        text = text.replace(old, new)
    return text


def main(argv):
    mode = "apply"
    force = False
    path = None
    for arg in argv[1:]:
        if arg == "--check":
            mode = "check"
        elif arg == "--dry-run":
            mode = "dry-run"
        elif arg == "--restore":
            mode = "restore"
        elif arg == "--force":
            force = True
        elif arg.startswith("--"):
            print(f"unknown option: {arg}")
            return 2
        else:
            path = arg
    if path is None:
        path = find_default_path()
    if path is None:
        print("bundle not found - pass its path as an argument")
        return 2
    backup = path + ".orig"

    if mode == "restore":
        if not os.path.exists(backup):
            print(f"no backup found ({backup}) - nothing to restore")
            return 1
        data = open(backup, "rb").read()
        digest = md5_of(data)
        if digest != STOCK_MD5:
            print(f"warning: backup MD5 is {digest}, not the reference stock {STOCK_MD5}")
        shutil.copyfile(backup, path)
        print(f"restored {path} from {backup} (MD5 {digest})")
        return 0

    if not os.path.exists(path):
        print(f"file not found: {path}")
        return 2
    raw = open(path, "rb").read()
    digest = md5_of(raw)
    print(f"bundle : {path}")
    print(f"MD5    : {digest}")

    if digest == PATCHED_MD5:
        print("status : already patched (reference build) - nothing to do")
        return 0
    if digest != STOCK_MD5:
        print("status : this is not the reference stock bundle")
        if not force:
            print("         re-run with --force to patch by anchors anyway, "
                  "or use the drop-in file from this repo instead")
            if mode == "check":
                return 1
        else:
            print("         --force given: anchors will decide")
    else:
        print("status : reference stock bundle")

    text = raw.decode("utf-8")
    try:
        patched = apply_patches(text)
    except RuntimeError as exc:
        print(f"FAILED : {exc}")
        return 1
    out_md5 = md5_of(patched.encode("utf-8"))
    print(f"anchors: all {len(PATCHES)} changes apply cleanly")
    print(f"result : MD5 {out_md5}" +
          (" (matches the tested patched bundle)" if out_md5 == PATCHED_MD5
           else " (differs from the reference patched bundle - expected on a non-stock build)"))

    if mode in ("check", "dry-run"):
        print(f"{mode}: no file was modified")
        return 0

    if digest != STOCK_MD5 and not force:
        return 1
    if not os.path.exists(backup):
        shutil.copyfile(path, backup)
        print(f"backup : {backup}")
    else:
        print(f"backup : {backup} already exists, kept as is")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(patched)
    print("patched: done - hard-refresh Fluidd in your browser (Ctrl+F5)")
    print("reminder: the filament table officiall_filas_list.cfg must also be")
    print("          installed in ~/printer_data/config/ - see README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
