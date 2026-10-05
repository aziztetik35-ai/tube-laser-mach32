"""Makro testleri:  python tests/test_macros.py
1) Her makro: cp1252 uyumu, If/For blok dengesi, tek satır If yok, çeviriciden geçiyor
2) M800: Python (vbrun) ile tarayıcı sürümü (vb2js -> m800.js, Node) satır satır AYNI G-kodu üretiyor
3) M800 geometri: delik ölçü/konum, kesim sırası, G0 ile kesim yok, X0 ve delik hata mesajları
4) Kaydet/Yükle (M803/M804) ve İçe aktar (M820) gidiş-dönüş
"""
import os, sys, re, json, glob, subprocess, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools")); import vbrun
MAC = lambda n: open(os.path.join(ROOT, "macros", n + ".bas"), encoding="utf-8").read()
BASE = {1000: 1, 1001: 50, 1002: 40, 1003: 40, 1004: 2, 1005: 3, 1006: 45, 1007: 45, 1008: 60, 1009: 1200, 1010: 0.3, 1011: 0.2,
        1012: 25, 1013: 1, 1014: 800, 1015: 2, 1016: 2, 1017: 300, 1018: 1, 1019: 1, 1022: 3, 1023: 1, 1030: 0, 1031: 0, 1032: 60, 1033: 90}
PAR = {"VelocitiesX": 100, "VelocitiesY": 100, "VelocitiesZ": 50, "VelocitiesA": 60}
fails = []
def check(cond, msg):
    print(("  ok   " if cond else "  HATA ") + msg)
    if not cond: fails.append(msg)

def dro(kw, holes=()):
    d = dict(BASE); d.update(kw)
    for i, h in enumerate(holes):
        for j, v in enumerate(h): d[1100 + i * 10 + j] = v
    d[1039] = 1
    for c in range(7): d[1040 + c] = d.get(1100 + c, 0)
    return d

print("1) Makro sözdizimi")
for p in sorted(glob.glob(os.path.join(ROOT, "macros", "*.bas"))):
    n = os.path.basename(p); s = open(p, encoding="utf-8").read()
    try: s.encode("cp1252"); enc = True
    except UnicodeEncodeError: enc = False
    st, ok, single = [], True, None
    for i, l in enumerate(s.split("\n"), 1):
        l = vbrun.strip_comment(l).strip()
        if re.match(r"^If .* Then$", l, re.I): st.append("If")
        elif re.match(r"^If .* Then\s+\S", l, re.I): single = i
        elif l.lower() == "end if": ok &= bool(st) and st.pop() == "If"
        elif re.match(r"^For\s", l, re.I): st.append("For")
        elif re.match(r"^Next\b", l, re.I): ok &= bool(st) and st.pop() == "For"
        elif re.match(r"^(While|Wend|Do|Loop|Sub|Function|Select)\b", l, re.I): single = i
    try: compile(vbrun.transpile(s), n, "exec"); tr = True
    except Exception as e: tr = False
    check(enc and ok and not st and single is None and tr, f"{n}: cp1252={enc} blok={ok and not st} yasak_satır={single} çeviri={tr}")

print("2) M800 Python == tarayıcı (m800.js)")
subprocess.run([sys.executable, os.path.join(ROOT, "studio", "vb2js.py"), os.path.join(ROOT, "macros", "M800.bas"), os.path.join(ROOT, "studio", "m800.js")], check=True, capture_output=True)
HOLES = [(1, 100, 0, 0, 15, 0, 0), (2, 150, 90, 3, 24, 8, 0), (3, 200, 180, 0, 30, 14, 3)]
CASES = {"yuvarlak": dro({1000: 0}), "dikd_tek": dro({}), "dikd_kenar": dro({1019: 0, 1002: 60, 1003: 30}),
         "a1_a2": dro({1000: 0, 1007: 90, 1018: 3}), "balik": dro({1030: 1, 1031: 2, 1032: 50, 1033: 70, 1018: 2}),
         "delik_dikd": dro({1018: 2}, HOLES), "delik_yuv": dro({1000: 0, 1018: 2}, HOLES), "hata_x0": dro({1000: 0, 1008: 5})}
py = {}
for k, d in CASES.items():
    out, msgs, *_ = vbrun.run(MAC("M800"), dict(d), PAR, {}, shared=True); py[k] = out
tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump({k: {str(a): b for a, b in d.items()} for k, d in CASES.items()}, tmp); tmp.close()
js = subprocess.run(["node", "-e", "const {runM800}=require(process.argv[1]);const C=JSON.parse(require('fs').readFileSync(process.argv[2]));"
                     "const o={};for(const k in C)o[k]=runM800(C[k],JSON.parse(process.argv[3])).gcode;console.log(JSON.stringify(o))",
                     os.path.join(ROOT, "studio", "m800.js"), tmp.name, json.dumps(PAR)], capture_output=True, text=True)
jo = json.loads(js.stdout) if js.returncode == 0 else {}
for k in CASES: check(jo.get(k) == py[k], f"{k}: {len(py[k])} satır, JS aynı={jo.get(k) == py[k]}")

print("3) M800 geometri ve kurallar")
def groups(out):
    g, cur = {}, None
    for l in out:
        m = re.match(r"\(parca (\d+) - (.*)\)", l)
        if m: cur = (int(m.group(1)), m.group(2)); g[cur] = []; continue
        if cur and l.startswith("G1"): g[cur].append({k: float(v) for k, v in re.findall(r"([XYZA])(-?[\d.]+)", l)})
    return g
out, msgs, *_ = vbrun.run(MAC("M800"), CASES["delik_dikd"], PAR, {}, shared=True)
g = groups(out); x0, pitch = 60, 300 + 0.2
for (p, lab), pts in g.items():
    if not lab.startswith("delik"): continue
    n = int(lab.split()[1]); h = HOLES[n - 1]; pts = pts[1:]
    xs = [q["X"] for q in pts]; ys = [q["Y"] for q in pts]
    L = h[4]; W = h[4] if h[0] == 1 else h[5]
    cx = (max(xs) + min(xs)) / 2 - (x0 + (p - 1) * pitch)
    check(abs(cx - h[1]) < 0.01 and abs(max(xs) - min(xs) - L) < 0.01 and abs(max(ys) - min(ys) - W) < 0.01, f"parça {p} {lab}: merkez {cx:.2f} boy {max(xs)-min(xs):.2f} en {max(ys)-min(ys):.2f}")
order = [l for l in out if l.startswith("(parca")]
check(order.index("(parca 1 - delik 1)") < order.index([o for o in order if o.startswith("(parca 1 - gonye")][-1]), "delikler parça ayrılmadan önce kesiliyor")
mode, laser, bad = 0, False, 0
for l in out:
    if l.startswith("M3"): laser = True
    if l.startswith("M5"): laser = False
    if re.match(r"G0\b", l): mode = 0
    if re.match(r"G1\b", l): mode = 1
    if laser and mode == 0 and re.search(r"[XYZA]-?\d", l) and not l.startswith("G0 Z"): bad += 1
check(bad == 0, f"lazer açıkken G0 hareketi yok ({bad})")
xs = [float(re.search(r"x([\d.]+)", l).group(1)) for l in out if re.match(r"\(parca \d+ - gonye", l)]
check(xs == sorted(xs), "kesim sırası boru ucundan aynaya (X artan)")
_, msgs, *_ = vbrun.run(MAC("M800"), CASES["hata_x0"], PAR, {}, shared=True)
check(msgs[-1].startswith("HATA: X0 en az"), "küçük X0 hatası: " + msgs[-1][:50])
_, msgs, *_ = vbrun.run(MAC("M800"), dro({1017: 150}, HOLES), PAR, {}, shared=True)
check("Delik 3" in msgs[-1], "parça dışı delik hatası: " + msgs[-1][:50])

print("4) Kaydet/Yükle ve İçe aktar")
st = dro({1000: 1, 1018: 2}, HOLES); files = {}; labels = {}
vbrun.run(MAC("M803"), st, PAR, files, shared=True, labels=labels)
saved = {k: st.get(k, 0) for k in list(range(1100, 1127)) + [1000, 1018]}
for k in range(1100, 1298): st[k] = 0
vbrun.run(MAC("M804"), st, PAR, files, shared=True, labels=labels)
check(all(abs(st.get(k, 0) - v) < 1e-9 for k, v in saved.items()), "M803 -> M804 delikler geri geldi")
cfg = ["TUBESTUDIO 1", "1000=0", "1001=60", "1018=3", "1100=2", "1101=80", "1104=20", "1105=6", "END"]
files = {"C:\\Mach3\\Addons\\TubeStudio\\tubecut_config.txt": cfg}; st = dro({}); labels = {}
_, msgs, *_ = vbrun.run(MAC("M820"), st, PAR, files, shared=True, labels=labels)
check(st[1001] == 60 and st[1100] == 2 and st[1041] == 80 and "Yuvarlak" in labels.get(31, ""), "M820 içe aktarma: " + msgs[-1][:45])

print("\nSONUÇ:", "BAŞARILI" if not fails else f"{len(fails)} HATA")
sys.exit(1 if fails else 0)
