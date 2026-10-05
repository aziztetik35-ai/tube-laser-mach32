"""dist/Mach3 içeriğini Mach3 kurulumuna kopyalar (önce yedek alır).
   python tools/install.py --mach3 "C:\\Mach3" --profile Mach3Mill [--dry-run]
Makrolar macros\\<profil>\\ altına, wizard'lar Addons\\ altına gider.
Kullanıcı verileri (tubecut.dat, tubecut_config.txt, wizard_state.js, tubesim_data.js) üzerine yazılmaz."""
import os, sys, shutil, argparse, datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "dist", "Mach3")
ap = argparse.ArgumentParser(); ap.add_argument("--mach3", required=True); ap.add_argument("--profile", required=True)
ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
if not os.path.isdir(SRC): raise SystemExit("Önce: python tools/build_all.py")
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bak = os.path.join(a.mach3, "_yedek_tubelaser_" + stamp)
plan = []
for f in os.listdir(os.path.join(SRC, "macros")):
    plan.append((os.path.join(SRC, "macros", f), os.path.join(a.mach3, "macros", a.profile, f)))
for w in os.listdir(os.path.join(SRC, "Addons")):
    for f in os.listdir(os.path.join(SRC, "Addons", w)):
        plan.append((os.path.join(SRC, "Addons", w, f), os.path.join(a.mach3, "Addons", w, f)))
for s, d in plan:
    print(("[deneme] " if a.dry_run else "") + d)
    if a.dry_run: continue
    if os.path.exists(d):
        b = os.path.join(bak, os.path.relpath(d, a.mach3)); os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copy2(d, b)
    os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)
print("Yedek:", bak if not a.dry_run else "-", "\nMach3'ü yeniden başlatın (arka plan resimleri açılışta yüklenir).")
