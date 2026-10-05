"""tubesim.html (bağımsız simülasyon sayfası) üretir: python sim/build.py <çıktı.html>"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
rd = lambda *p: open(os.path.join(*p), encoding="utf-8").read()
sh = rd(HERE, "shell.html")
libs = "".join("<script>\n" + rd(ROOT, *p) + "\n</script>\n" for p in [("vendor", "three", "three.min.js"), ("vendor", "three", "OrbitControls.js"), ("sim", "core.js")])
sh = sh.replace("<!--THREE-->", libs).replace("<!--APP-->", "<script>\n" + rd(HERE, "app.js") + "\n</script>")
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "tubesim.html")
open(out, "w", encoding="utf-8").write(sh); print("tubesim.html", len(sh))
