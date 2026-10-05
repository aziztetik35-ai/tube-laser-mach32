"""tubestudio.html üretir. M800.bas -> m800.js (vb2js) çevrilir; önizleme Mach3 ile aynı makroyu çalıştırır.
python studio/build.py <çıktı.html>"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
subprocess.run([sys.executable, os.path.join(HERE, "vb2js.py"), os.path.join(ROOT, "macros", "M800.bas"), os.path.join(HERE, "m800.js")], check=True)
rd = lambda *p: open(os.path.join(*p), encoding="utf-8").read()
sh = rd(HERE, "shell.html")
libs = "".join("<script>\n" + rd(ROOT, *p) + "\n</script>\n" for p in [("vendor", "three", "three.min.js"), ("vendor", "three", "OrbitControls.js"),
                                                                    ("sim", "core.js"), ("studio", "m800.js"), ("studio", "viewer.js"), ("studio", "editor.js")])
sh = sh.replace("<!--LIBS-->", libs).replace("<!--APP-->", "<script>\n" + rd(HERE, "studio.js") + "\n</script>")
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "tubestudio.html")
open(out, "w", encoding="utf-8").write(sh); print("tubestudio.html", len(sh))
