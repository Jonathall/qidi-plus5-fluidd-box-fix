#!/usr/bin/env python3
"""
QIDI Plus 5 - Fluidd Box & External Spool Fix - bundle patcher (firmware 01.01.02.02)

Patches the stock Fluidd bundle shipped with QIDI Plus 5 firmware
01.01.02.02 (assets/index-nyEzQB9T.js, Fluidd v1.30.5) so the Control Box
panel, the external spool (slot 16) and the print dialog work with the
current firmware, which identifies filaments by QIDI filament IDs
(QFA00, QFL31...) and hex colors instead of the legacy numeric format
the bundled Fluidd still expects.

This is the V10 build of the fix: the 16 anchored replacements of the
original patcher (V9.4, for the firmware 01.01.02.01 bundle) ported to
the new bundle build, plus 10 restoration steps. Firmware 01.01.02.02
dereferenced the two filament-editing surfaces of Fluidd - the
dashboard Box card and the print-time filament assignment dialog -
without removing their code; the restoration steps re-register and
re-assemble them from the code that still ships in the bundle, on top
of the .02 code (every .02 behavior, including the spoolman dialog
branch and the simplified no-box upload flow, is preserved).

The patch is a set of 26 anchored replacements (each anchor must be
found exactly once, or the script refuses to touch the file). On the
reference stock bundle it reproduces the tested patched bundle byte
for byte.

For any firmware, the unified patcher qidi_plus5_fluidd_fix.py detects
the bundle build and dispatches to the right engine; this file can also
be run directly.

Usage:
  python3 qidi_plus5_fluidd_fix_010202.py [path/to/index-nyEzQB9T.js]  apply (keeps a .orig backup)
  python3 qidi_plus5_fluidd_fix_010202.py --check    [path]            verify only, change nothing
  python3 qidi_plus5_fluidd_fix_010202.py --dry-run  [path]            simulate, change nothing
  python3 qidi_plus5_fluidd_fix_010202.py --restore  [path]            restore the .orig backup
  python3 qidi_plus5_fluidd_fix_010202.py --force    [path]            apply even if the bundle is
                                                                       not the reference stock build
                                                                       (anchors are still verified)

Default path: ./index-nyEzQB9T.js if present, else ~/fluidd/assets/index-nyEzQB9T.js
(run it on your PC against a downloaded copy, or on the printer over SSH).

IMPORTANT: the bundle is only half of the fix. The filament table
officiall_filas_list.cfg (see the drop-in folder) must also be installed
in ~/printer_data/config/ on the printer. It is unchanged from V9.4.
See README.md.

License: GPL-3.0 (Fluidd and QIDI's Klipper/Moonraker editions are GPL-3.0;
this patch is distributed under the same terms).
"""
import hashlib
import os
import shutil
import sys

STOCK_MD5 = "c655b6a006d1e9a1e97b188e9f4cde05"    # reference stock bundle (Fluidd v1.30.5, Plus 5 firmware 01.01.02.02)
PATCHED_MD5 = "74eae054f918ca7b05b41f3811590ef0"  # expected result on the reference stock bundle (V10)

PATCHES = [
    # --- change 1 (.02: .every callback renamed t->e in the anchor; replacement unchanged) ---
    ('get isOkPrinter(){return this.enableBox===!1?this.$store.state.printer.printer.box_extras.e_endstop_state===1?this.$store.state.printer.printer.box_extras.b_endstop_state===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(e=>this.selectedValueSlot[e]))}',
     'get isOkPrinter(){return this.enableBox===!1?((this.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"]||{}).filament_detected===!0)?(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot[t]))}'),
    # --- change 2 (verbatim) ---
    ('for(const s in this.officialFilasListDictData)s.startsWith("fila")&&t.add(this.officialFilasListDictData[s].filament);',
     'const cv=this.items&&this.items[this.selectIndex]?this.items[this.selectIndex].vendor:null;for(const s in this.officialFilasListDictData){if(!s.startsWith("fila"))continue;const e=this.officialFilasListDictData[s];if(cv&&e.vendor!==cv)continue;t.add(e.filament)}if(t.size===0)for(const s in this.officialFilasListDictData)s.startsWith("fila")&&t.add(this.officialFilasListDictData[s].filament);'),
    # --- change 3 (verbatim) ---
    ('get isOperating(){const t=this.$store.state.printer.printer.box_extras;return!(!t||!t.box_button_state)}',
     'get isOperating(){const t=this.$store.state.printer.printer.multi_color_controller;return!(!t||!t.operation||!t.operation.box_button_state)}'),
    # --- change 4 (verbatim) ---
    ('return this.selectIndex>=16||(this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0),t}',
     'if(this.selectIndex>=16){const D=(this.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"]||{}).filament_detected===!0;t[1]=D,t[2]=!D}else this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&(((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0;return t}'),
    # --- change 5 (.02: socket alias I->R in anchor and replacement) ---
    ('s&&(this.selectIndex===16?R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot16 VALUE="${s}"`):R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${s}"`))}get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t&&(this.selectIndex===16?R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot16 VALUE="${s.replace("fila","")}"`):R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${s.replace("fila","")}"`))}',
     'const cur=(this.items||[])[this.selectIndex]||{},nm=cur.filament;let hit=null,typ=null;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(!e||!e.filament_id)continue;if(e.vendor===t&&e.filament===nm)hit=e;if(e.vendor===cur.vendor&&e.filament===nm)typ=e.type}if(!hit&&typ){for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.vendor===t&&e.type===typ){hit=e;break}}}if(!hit){for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.vendor===t){hit=e;break}}}if(hit)R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="\'${hit.filament_id}\'"`)}\nget selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){let q=null;const cv=((this.items||[])[this.selectIndex]||{}).vendor;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.filament===t&&e.vendor===cv){q=e.filament_id;break}}if(!q)for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.filament_id&&e.filament===t){q=e.filament_id;break}}const bx=(this.$store.state.printer.printer.box_extras||{}).boxes||[];if(!q)for(const b of bx){const fis=(b&&b.filament_info)||[];for(const fi of fis)if(fi&&fi.filament_str===t&&fi.filament_id){q=fi.filament_id;break}if(q)break}if(!q){const ex=((this.$store.state.printer.printer.multi_color_controller||{}).extra||{}).filament_info;if(ex&&ex.filament_str===t&&ex.filament_id)q=ex.filament_id}let w=null;for(const k in this.officialFilasListDictData){const e=this.officialFilasListDictData[k];if(e&&e.vendor&&e.filament===t){w=this.getKeyByValue(this.officialFilasListDictData.vendor_list,e.vendor);break}}for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t&&(this.selectIndex===16?R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot16 VALUE="${q?"\'"+q+"\'":"\'"+(this.officialFilasListDictData[s].filament_id||s.replace("fila",""))+"\'"}"`):(R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${q?"\'"+q+"\'":s.replace("fila","")}"`), w&&R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${w}"`)))}'),
    # --- change 6 (.02: socket alias I->R in anchor and replacement) ---
    ('s&&(this.selectIndex===16?R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot16 VALUE="${s}"`):R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="${s}"`))}',
     's&&(this.selectIndex===16?R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot16 VALUE="[\'${String(t).replace("#","")}\']"`):R.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="[\'${String(t).replace("#","")}\']"`))}'),
    # --- change 7 (verbatim) ---
    ('s[v]=parseInt(e[g]??"0",10)}',
     'const V=e[g];let hx=null;if(Array.isArray(V))hx=V[0]?"#"+V[0]:"";else if(typeof V==="string"&&V.charAt(0)==="[")hx="#"+V.replace(/[\\[\\]\'"\\s]/g,"");if(hx&&hx.length>=7){const cd=((r.officiallFilasList||{}).colordict)||{},fk=Object.keys(cd).find(k=>String(cd[k]).toUpperCase()===hx.toUpperCase());s[v]=fk?parseInt(fk,10):0;hx2[v]=hx.toUpperCase()}else if(hx!==null)s[v]=0;else s[v]=parseInt(V??"0",10)}'),
    # --- change 8 (verbatim) ---
    ('n[v]=parseInt(e[g]??"0",10)}',
     'const V=e[g];if(typeof V==="string"&&isNaN(parseInt(V,10))){const cat=r.officiallFilasList||{},dk=Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament_id===V);if(dk)n[v]=parseInt(dk.replace("fila",""),10);else{const bx=(r.printer.box_extras||{}).boxes||[];let nm=null;for(const b of bx){const fis=(b&&b.filament_info)||[];for(const fi of fis)if(fi&&fi.filament_id===V){nm=fi.filament_str;break}if(nm)break}if(!nm){const bz=bx[Math.floor(v/4)],fi=bz&&bz.filament_info?bz.filament_info[v%4]:null;nm=fi?fi.filament_str:null}const fk=nm?Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament===nm):null;n[v]=fk?parseInt(fk.replace("fila",""),10):0}}else n[v]=parseInt(V??"0",10)}'),
    # --- change 9 (verbatim) ---
    ('i[v]=parseInt(e[g]??"0",10)}',
     'const FV=e["filament_slot"+v];if(typeof FV==="string"&&isNaN(parseInt(FV,10))){const cat=r.officiallFilasList||{},vl=cat.vendor_list||{},bx=(r.printer.box_extras||{}).boxes||[],bz=bx[Math.floor(v/4)],fi=bz&&bz.filament_info?bz.filament_info[v%4]:null,vs=fi?fi.vendor_str:null,fk=vs?Object.keys(vl).find(k=>vl[k]===vs):(()=>{const dk=Object.keys(cat).find(k=>k.startsWith("fila")&&cat[k]&&cat[k].filament_id===FV),ev=dk?cat[dk].vendor:null;return ev?Object.keys(vl).find(k=>vl[k]===ev):null})();i[v]=fk?parseInt(fk,10):parseInt(e[g]??"0",10)}else i[v]=parseInt(e[g]??"0",10)}'),
    # --- change 10 (verbatim) ---
    ('return a[16]=1,{boxCount:t,colorSlot:s,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:c,lastLoadSlot:u}',
     'return a[16]=1,{boxCount:t,colorSlot:s,colorHex:hx2,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:[s[16],n[16],i[16]],lastLoadSlot:u}'),
    # --- change 11 (verbatim) ---
    ('t=e.box_count??0,s=[],n=[],i=[],',
     't=e.box_count??0,s=[],n=[],i=[],hx2=[],'),
    # --- change 12 (.02: item builder locals renamed - result o, colordict a, index s) ---
    ('o=a?a[this.variables.colorSlot[s]]:"#000000"',
     'o=(this.variables.colorHex&&this.variables.colorHex[s])||(a?a[this.variables.colorSlot[s]]:"#000000")'),
    # --- change 13 (verbatim) ---
    ('C=((a=this.officialFilasListDictData)==null?void 0:a.colordict[String(this.variables.colorSlot[m])])??"#00000000"',
     'C=(this.variables.colorHex&&this.variables.colorHex[m])||(((a=this.officialFilasListDictData)==null?void 0:a.colordict[String(this.variables.colorSlot[m])])??"#00000000")'),
    # --- change 14 (verbatim) ---
    ('color:((u=this.officialFilasListDictData)==null?void 0:u.colordict[this.variables.rackExtra[0]])??"#00000000"',
     'color:(this.variables.colorHex&&this.variables.colorHex[16])||(((u=this.officialFilasListDictData)==null?void 0:u.colordict[this.variables.rackExtra[0]])??"#00000000")'),
    # --- change 15 (.02: VRow Y->K, VCol k->D, Iro picker $w->_w in the replacement; gh unchanged) ---
    ('e.handleColorClick(e.colorItems[n-1])}}})])}),1)',
     'e.handleColorClick(e.colorItems[n-1])}}})])}),1),t(K,{attrs:{align:"center",justify:"center"}},[t(D,{attrs:{cols:"auto"}},[t("div",{on:{click:function(t){t.stopPropagation()}}},[t(_w,{attrs:{options:{width:232,layout:[{component:gh.ui.Wheel,options:{wheelLightness:!1,wheelAngle:270,wheelDirection:"clockwise"}},{component:gh.ui.Slider,options:{sliderType:"value"}}]}},model:{value:e.selectedColor&&e.selectedColor!=="#00000000"?e.selectedColor:"#000000",callback:function(s){return e.handleColorClick(s.toUpperCase())},expression:"selectedColor"}}),t("div",{staticClass:"text-center"},[e._v(e._s(e.selectedColor||""))])])])])'),
    # --- change 16 (verbatim) ---
    ('set selectedColor(t){const s=this.getKeyByValue(this.officialFilasListDictData.colordict,t);',
     'set selectedColor(t){const s=1;'),
    # --- restoration R1 (V10): BoxCard wrapper render + assembly re-injected after the orphaned Dw class decoration (render adapted from .01: card component Xe->Je) ---
    ('Dw=mce([L({components:{Box:pce}})],Dw);',
     'Dw=mce([L({components:{Box:pce}})],Dw);var vB9=function(){var e=this,t=e._self._c;return e._self._setupProxy,t(Je,{attrs:{title:e.$t("app.box.label.title"),"help-tooltip":e.$t("app.box.tooltip.control_filament"),icon:"$abacus",draggable:"","layout-path":"dashboard.box-card"}},[t("box")],1)},sB9=[],aB9=A(Dw,vB9,sB9,!1,null,null);const wB9=aB9.exports;'),
    # --- restoration R2 (V10): BoxCard re-registered in the dashboard components registry ---
    ('components:{PrinterStatusCard:iK,',
     'components:{PrinterStatusCard:iK,BoxCard:wB9,'),
    # --- restoration R3 (V10): print dialog render + assembly re-injected after the orphaned ku class decoration (render adapted from .01 with the full .02 alias map; scoped CSS data-v-d6f4b985 still ships in the .02 CSS) ---
    ('ku=om([L({components:{FileSystemSelectLine:WY,FileSystemOutSelectLine:XY}})],ku);',
     'ku=om([L({components:{FileSystemSelectLine:WY,FileSystemOutSelectLine:XY}})],ku);var dR9=function(){var e=this,t=e._self._c;return e._self._setupProxy,t(rt,{attrs:{title:e.title,"max-width":"400"},scopedSlots:e._u([{key:"actions",fn:function(){return[t(ct),t(I,{attrs:{type:"button"},on:{click:function(s){return e.handleCancel()}}},[e._v(" "+e._s(e.$t("app.general.btn.cancel"))+" ")]),t(I,{attrs:{color:"primary",disabled:!e.isOkPrinter,type:"button"},on:{click:function(s){return e.handlePrint()}}},[e._v(" "+e._s(e.$t("app.general.btn.print"))+" ")])]},proxy:!0}]),model:{value:e.open,callback:function(s){e.open=s},expression:"open"}},[t(Pe,[t(K,[t(D,[e.isOkPrinter?e._e():t(Fi,{attrs:{text:"",outlined:"",border:"left","colored-border":"",color:e.$vuetify.theme.currentTheme.primary}},[e._v(e._s(e.error_msg))])],1)],1),t(K,[t(D,[t("div",{staticClass:"image-container"},[t(F8,{staticClass:"mb-4",attrs:{src:e.url||e.imgUrl,alt:"Filesystem Image","max-height":"150","max-width":"150"}}),t(zb,{attrs:{bottom:"",small:"",tooltip:e.$t("app.file_system.tooltip.tip")}})],1)])],1),t(K,[t(D,[t(Ie,{attrs:{outlined:""}},[t(K,[t(D,{attrs:{align:"center"}},[t(x,[e._v("$clock")]),e._v(" "+e._s(e.formatSeconds(e.fileMeta.estimated_time))+" ")],1),t(D,{attrs:{align:"center"}},[t(x,[e._v("$gold")]),e._v(" "+e._s(e.fileMeta.filament_weight_total||"?")+" g ")],1)],1),t(Pe,[e.enableBox?t("file-system-select-line",{attrs:{"used-extruders":e.usedExtruders,"file-colors":e.filecolors,"file-labels":e.filelabels,items:e.items,"selected-value-slot":e.selectedValueSlot},on:{"value-change":e.onValueChange}}):t("file-system-out-select-line",{attrs:{"used-extruders":e.usedExtruders,"file-colors":e.filecolors,"file-labels":e.filelabels}})],1)],1)],1)],1),t(K,{attrs:{height:"40px"}},[t(D,{attrs:{cols:"auto"}},[t(lr,{attrs:{"hide-details":"auto",dense:""},scopedSlots:e._u([{key:"label",fn:function(){return[t("span",{staticClass:"label-text"},[e._v(e._s(e.$t("app.file_system.label.enable_box")))])]},proxy:!0}]),model:{value:e.enableBox,callback:function(s){e.enableBox=s},expression:"enableBox"}})],1)],1)],1)],1)},dS9=[],dA9=A(ku,dR9,dS9,!1,null,"d6f4b985");const dE9=dA9.exports;'),
    # --- restoration R4 (V10): dialog re-registered in the print status component (hf) ---
    ('ReprintTab:BY}})],hf);',
     'ReprintTab:BY,FileSystemSelectLineDialog:dE9}})],hf);'),
    # --- restoration R5 (V10): dialog re-registered in the files component (Es) ---
    ('FilePreviewDialog:j6}})],Es);',
     'FilePreviewDialog:j6,FileSystemSelectLineDialog:dE9}})],Es);'),
    # --- restoration R6 (V10): dialog re-registered in the app component (Cy) ---
    ('AppUploadAndPrintBtn:$L}})],Cy);',
     'AppUploadAndPrintBtn:$L,FileSystemSelectLineDialog:dE9}})],Cy);'),
    # --- restoration R7a (V10): box branch of hf.handlePrint restored on the .02 body (spoolman branch and .02 fallthrough kept) ---
    ('if(s&&n){this.$store.commit("spoolman/setDialogState",{show:!0,filename:t});return}R.printerPrintStart(t)}',
     'if(s&&n){this.$store.commit("spoolman/setDialogState",{show:!0,filename:t});return}if(this.$store.state.printer.printer.save_variables.variables.box_count&&this.$store.getters["files/getCanPrint"]("gcodes",t)){this.FileSystemSelectLineDialogState={open:!0,filename:t};return}R.printerPrintStart(t)}'),
    # --- restoration R7b (V10): box branch of Es.handlePrint restored on the .02 body (spoolman branch and .02 fallthrough kept) ---
    ('if(n&&i){this.$store.commit("spoolman/setDialogState",{show:!0,filename:s});return}R.printerPrintStart(s),this.$router.currentRoute.path!=="/"&&this.$router.push({path:"/"})}',
     'if(n&&i){this.$store.commit("spoolman/setDialogState",{show:!0,filename:s});return}if(this.$store.state.printer.printer.save_variables.variables.box_count&&this.$store.getters["files/getCanPrint"](this.currentRoot,s)){this.FileSystemSelectLineDialogState={open:!0,filename:s};return}R.printerPrintStart(s),this.$router.currentRoute.path!=="/"&&this.$router.push({path:"/"})}'),
    # --- restoration R8a (V10): box branch of Es.handleUpload restored (the .01 body is the .02 body plus the branch; no-box path identical) ---
    ('async handleUpload(t,s){const n=`${this.$waits.onFileSystem}/${this.currentPath}/`;this.$store.dispatch("wait/addWait",n),await this.uploadFiles(t,this.visiblePath,this.currentRoot,s),this.$store.dispatch("wait/removeWait",n)}',
     'async handleUpload(t,s){const n=`${this.$waits.onFileSystem}/${this.currentPath}/`;if(this.$store.dispatch("wait/addWait",n),this.$store.state.printer.printer.save_variables.variables.box_count&&s){await this.uploadFiles(t,this.visiblePath,this.currentRoot,!1);let i="";for(const o of t){const[l,c]=this.getFullPathAndFile(this.visiblePath,o);i=l?`${l}/${c.name}`:c.name}this.$store.getters["files/getCanPrint"](this.currentRoot,i)&&(this.FileSystemSelectLineDialogState={open:!0,filename:i})}else await this.uploadFiles(t,this.visiblePath,this.currentRoot,s);this.$store.dispatch("wait/removeWait",n)}'),
    # --- restoration R8b (V10): box branch of Cy.handleUploadAndPrint restored alongside the .02 body (no box -> .02 upload-and-print kept verbatim in the else branch) ---
    ('handleUploadAndPrint(e){this.uploadFile(e,"/","gcodes",!0)}',
     'handleUploadAndPrint(e){if(this.$store.state.printer.printer.save_variables.variables.box_count){this.uploadFile(e,"","gcodes",!1);let t="";const[s,n]=this.getFullPathAndFile("",e);t=s?`${s}/${n.name}`:n.name,this.$store.getters["files/getCanPrint"]("gcodes",t)&&(this.FileSystemSelectLineDialogState={open:!0,filename:t})}else this.uploadFile(e,"/","gcodes",!0)}'),
]


def md5_of(data):
    return hashlib.md5(data).hexdigest()


def find_default_path():
    for cand in ("index-nyEzQB9T.js",
                 os.path.expanduser("~/fluidd/assets/index-nyEzQB9T.js")):
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
