#!/usr/bin/env python3
"""
QIDI Plus 5 - Fluidd Box & External Spool Fix - unified bundle patcher

One entry point for every supported firmware. This script identifies the
Fluidd bundle you point it at - by MD5 first, then by file name - and
dispatches to the patcher engine for that bundle build:

  index-DlFvHGAh.js   firmware 01.01.02.01
                      -> qidi_plus5_fluidd_fix_010201.py
  index-nyEzQB9T.js   firmware 01.01.02.02
                      -> qidi_plus5_fluidd_fix_010202.py

Both engines must sit in the same folder as this script. Any bundle build
that is not recognized is refused, untouched: each engine only ever
patches the exact stock build it was written for, and verifies every
anchor before writing anything.

Usage (identical to the engines):
  python3 qidi_plus5_fluidd_fix.py [path/to/bundle.js]        apply (keeps a .orig backup)
  python3 qidi_plus5_fluidd_fix.py --check    [path]          verify only, change nothing
  python3 qidi_plus5_fluidd_fix.py --dry-run  [path]          simulate, change nothing
  python3 qidi_plus5_fluidd_fix.py --restore  [path]          restore the .orig backup
  python3 qidi_plus5_fluidd_fix.py --force    [path]          apply even if the bundle is
                                                              not the reference stock build
                                                              (anchors are still verified)

Default path: ./index-DlFvHGAh.js or ./index-nyEzQB9T.js if present,
else the same names under ~/fluidd/assets/.

IMPORTANT: the bundle is only half of the fix. The filament table
officiall_filas_list.cfg (see the drop-in folder for your firmware) must
also be installed in ~/printer_data/config/ on the printer. See README.md.

License: GPL-3.0 (Fluidd and QIDI's Klipper/Moonraker editions are GPL-3.0;
this patcher and the patched bundle are distributed under the same terms).
"""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# bundle MD5 -> engine script (stock and already-patched builds, so that
# --check / --restore also dispatch correctly on a patched bundle)
BY_MD5 = {
    "b9bc4faaf367d0603d92d7217476c57a": "qidi_plus5_fluidd_fix_010201.py",  # stock  .01
    "3a4a3f3123154bd0a30983a345263fd5": "qidi_plus5_fluidd_fix_010201.py",  # patched .01
    "c655b6a006d1e9a1e97b188e9f4cde05": "qidi_plus5_fluidd_fix_010202.py",  # stock  .02
    "74eae054f918ca7b05b41f3811590ef0": "qidi_plus5_fluidd_fix_010202.py",  # patched .02
}

# bundle file name -> engine script (fallback when the MD5 is unknown,
# e.g. --force on a rebuilt bundle: the engine still verifies its anchors)
BY_NAME = {
    "index-DlFvHGAh.js": "qidi_plus5_fluidd_fix_010201.py",
    "index-nyEzQB9T.js": "qidi_plus5_fluidd_fix_010202.py",
}

SUPPORTED = (
    "supported bundles:\n"
    "  index-DlFvHGAh.js  (firmware 01.01.02.01, "
    "stock MD5 b9bc4faaf367d0603d92d7217476c57a)\n"
    "  index-nyEzQB9T.js  (firmware 01.01.02.02, "
    "stock MD5 c655b6a006d1e9a1e97b188e9f4cde05)"
)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_default_path():
    for name in BY_NAME:
        for cand in (name, os.path.expanduser(f"~/fluidd/assets/{name}")):
            if os.path.exists(cand):
                return cand
    return None


def pick_engine(path):
    digest = md5_of(path)
    if digest in BY_MD5:
        return BY_MD5[digest], f"MD5 {digest}"
    name = os.path.basename(path)
    if name in BY_NAME:
        return BY_NAME[name], f"file name {name} (MD5 {digest} not recognized)"
    return None, f"MD5 {digest}"


def main(argv):
    path = None
    for arg in argv[1:]:
        if not arg.startswith("--"):
            path = arg
    if path is None:
        path = find_default_path()
    if path is None:
        print("bundle not found - pass its path as an argument")
        print(SUPPORTED)
        return 2
    if not os.path.exists(path):
        print(f"file not found: {path}")
        return 2
    engine, how = pick_engine(path)
    if engine is None:
        print(f"unrecognized bundle: {path} ({how}) - refusing to patch")
        print(SUPPORTED)
        return 2
    engine_path = os.path.join(HERE, engine)
    if not os.path.exists(engine_path):
        print(f"patcher engine missing: {engine_path}")
        return 2
    print(f"bundle identified by {how} -> {engine}")
    return subprocess.call([sys.executable, engine_path] + argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
