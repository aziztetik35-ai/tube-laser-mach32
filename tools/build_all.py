"""Her şeyi derler: dist/Mach3/ altına Mach3 klasör düzeninde.
   python tools/build_all.py
Çıktı:
  dist/Mach3/macros/*.m1s                       (cp1252 + CRLF; profil klasörüne kopyalanır)
  dist/Mach3/Addons/TubeCutting/                 klasik wizard (2 sayfa) + tubesim.html
  dist/Mach3/Addons/TubeStudio/                  Tube Studio wizard + tubestudio.html
  dist/Mach3/Addons/TubeMill/                    boru freze wizard'ı + tubemillsim.html (mill/; makrolar M900-M909)
  dist/previews/                                 ekran önizleme PNG'leri ve yerleşim CSV'leri
Ayrıca dist/Mach3 içeriği depo kökündeki Mach3/ klasörüne kopyalanır (git'te tutulur, elle kopyalamak için):
  Mach3/macros/Mach3Mill/*.m1s, Mach3/Addons/TubeCutting/, Mach3/Addons/TubeStudio/
"""
import os, sys, glob, shutil, subprocess, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DIST = os.path.join(ROOT, "dist"); M3 = os.path.join(DIST, "Mach3")
PY = sys.executable

def run(args, cwd):
    r = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); raise SystemExit("HATA: " + " ".join(args))

def build_macros():
    out = os.path.join(M3, "macros"); os.makedirs(out, exist_ok=True)
    for src in sorted(glob.glob(os.path.join(ROOT, "macros", "*.bas")) + glob.glob(os.path.join(ROOT, "mill", "macros", "*.bas"))):
        t = open(src, encoding="utf-8").read().replace("\r\n", "\n")
        for i, line in enumerate(t.split("\n"), 1):
            try: line.encode("cp1252")
            except UnicodeEncodeError as e:
                raise SystemExit(f"HATA {os.path.basename(src)}:{i}: cp1252 dışı karakter {line[e.start]!r} (ı ş ğ İ Ş Ğ kullanmayın)")
        open(os.path.join(out, os.path.basename(src)[:-4] + ".m1s"), "wb").write(t.replace("\n", "\r\n").encode("cp1252"))
    print("makrolar:", len(glob.glob(os.path.join(out, "*.m1s"))))

PROFILE = "Mach3Mill"

def sync_repo_copy():
    """dist/Mach3 -> <depo>/Mach3 (makrolar profil klasörüne). Klasör her derlemede yeniden yazılır."""
    dst = os.path.join(ROOT, "Mach3")
    if os.path.isdir(dst): shutil.rmtree(dst)
    shutil.copytree(os.path.join(M3, "Addons"), os.path.join(dst, "Addons"))
    shutil.copytree(os.path.join(M3, "macros"), os.path.join(dst, "macros", PROFILE))
    print("Depo kopyası ->", dst)

def build_wizard(name, gens, setscript, keep):
    d = os.path.join(M3, "Addons", name); os.makedirs(d, exist_ok=True)
    pv = os.path.join(DIST, "previews"); os.makedirs(pv, exist_ok=True)
    for g in gens: run([os.path.join(ROOT, g)], d)
    run([os.path.join(ROOT, setscript)], d)
    for f in os.listdir(d):                       # önizleme ve ara dosyaları ayır
        if f not in keep: shutil.move(os.path.join(d, f), os.path.join(pv, f))
    print(name + ":", sorted(os.listdir(d)))

if __name__ == "__main__":
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    build_macros()
    build_wizard("TubeCutting", ["wizard/tubecutting/gen_page1.py", "wizard/tubecutting/gen_page2.py"], "wizard/tubecutting/build_set.py",
                 {"TubeCutting.set", "tube_wizard_bg.bmp", "tube_wizard_sayfa2.bmp"})
    run([os.path.join(ROOT, "sim", "build.py"), os.path.join(M3, "Addons", "TubeCutting", "tubesim.html")], ROOT)
    build_wizard("TubeStudio", ["wizard/tubestudio/gen_bg.py"], "wizard/tubestudio/build_set.py", {"TubeStudio.set", "tubestudio_bg.bmp"})
    run([os.path.join(ROOT, "studio", "build.py"), os.path.join(M3, "Addons", "TubeStudio", "tubestudio.html")], ROOT)
    build_wizard("TubeMill", ["mill/wizard/gen_page1.py", "mill/wizard/gen_page2.py"], "mill/wizard/build_set.py",
                 {"TubeMill.set", "tubemill_bg.bmp", "tubemill_sayfa2.bmp"})
    run([os.path.join(ROOT, "sim", "build.py"), os.path.join(M3, "Addons", "TubeMill", "tubemillsim.html"), "tubemill_data.js"], ROOT)
    sync_repo_copy()
    print("Bitti ->", M3)
