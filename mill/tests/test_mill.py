"""TubeMill makro testleri:  python mill/tests/test_mill.py
1) Sözdizimi: cp1252, If/For dengesi, yasak yapı yok, çeviriciden geçiyor; MILL-LED bloğu her makroda aynı
2) Uç kesimi: takım telafisi (net parça boyu), derinlik, kesim sırası, eğik kenarda takım-kenar mesafesi = rt
3) Delikler: kontur ölçüsü, delme (gagalama), yiv, tırmanma / konvansiyonel yönü, derinlik
4) Güvenlik: G0 ile malzemede yan hareket yok, iş mili kesimden önce açık, G93 satırlarında F var
5) Hata mesajları ve seçim makroları (M902-M906)
"""
import os, sys, re, glob, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools")); import vbrun
MAC = lambda n: open(os.path.join(ROOT, "mill", "macros", n + ".bas"), encoding="utf-8").read()
fails = []
def check(cond, msg):
    print(("  ok   " if cond else "  HATA ") + msg)
    if not cond: fails.append(msg)

BASE = {}
vbrun.run(MAC("M901"), BASE, {}, {}, shared=True)
def dro(kw, holes=()):
    d = dict(BASE); d.update(kw)
    for i, h in enumerate(holes):
        for j, v in enumerate(h): d[1600 + i * 10 + j] = v
    return d
def gen(d):
    out, msgs, leds, *_ = vbrun.run(MAC("M900"), dict(d), {}, {}, shared=True)
    return out, msgs, leds

def parse(out):
    """G-kodu sırayla oku: her G0/G1 hareketinin sonrasındaki konum, grup etiketi."""
    pos = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0}; moves = []; grp = None; spindle = False; gm = 94
    for l in out:
        m = re.match(r"\(parca (\d+) - (.*?)( x[-\d.]+)?\)", l)
        if m: grp = (int(m.group(1)), m.group(2)); continue
        if l.startswith("M3"): spindle = True
        if l.startswith("M5"): spindle = False
        if l == "G93": gm = 93
        if l == "G94": gm = 94
        g = re.match(r"G([01])\b", l)
        if not g: continue
        prev = dict(pos)
        for k, v in re.findall(r"([XYZAF])(-?[\d.]+)", l):
            if k != "F": pos[k] = float(v)
        moves.append(dict(g=int(g.group(1)), prev=prev, pos=dict(pos), grp=grp, spindle=spindle, gm=gm, F="F" in l, line=l))
    return moves

print("1) Makro sözdizimi")
blocks = {}
for p in sorted(glob.glob(os.path.join(ROOT, "mill", "macros", "*.bas"))):
    n = os.path.basename(p); s = open(p, encoding="utf-8").read()
    try: s.encode("cp1252"); enc = True
    except UnicodeEncodeError: enc = False
    st, ok, single = [], True, None
    for i, l in enumerate(s.split("\n"), 1):
        l = vbrun.strip_comment(l).strip()
        if re.match(r"^If .* Then$", l, re.I): st.append("If")
        elif re.match(r"^If .* Then\s+\S", l, re.I): single = i
        elif re.match(r"^ElseIf\b", l, re.I): single = i
        elif l.lower() == "end if": ok &= bool(st) and st.pop() == "If"
        elif re.match(r"^For\s", l, re.I): st.append("For")
        elif re.match(r"^Next\b", l, re.I): ok &= bool(st) and st.pop() == "For"
        elif re.match(r"^(While|Wend|Do|Loop|Sub|Function|Select)\b", l, re.I): single = i
    try: compile(vbrun.transpile(s), n, "exec"); tr = True
    except Exception: tr = False
    check(enc and ok and not st and single is None and tr, f"{n}: cp1252={enc} blok={ok and not st} yasak_satır={single} çeviri={tr}")
    m = re.search(r"'--- MILL-LED basla.*?'--- MILL-LED bitti", s, re.S)
    blocks[n] = m.group(0) if m else None
check(all(blocks.values()) and len(set(blocks.values())) == 1, "MILL-LED bloğu M900-M906'da aynı (%d makro)" % len(blocks))

print("2) Uç kesimi")
# dikdörtgen 60×30, 90°, 2 parça, takım 6: kesim ortak çizgi, aralık L + takım Ø
rt = 3; t = 2; ov = 0.5
d = dro({1500: 1, 1502: 60, 1503: 30, 1504: t, 1505: 1, 1510: 2, 1509: 100, 1508: 10})
out, msgs, _ = gen(d); mv = parse(out)
cutx = {}
for m in mv:
    if m["g"] == 1 and m["grp"] and "kesimi" in m["grp"][1]: cutx.setdefault(m["grp"], set()).add(m["pos"]["X"])
xs = [sorted(v) for v in cutx.values()]
check(all(len(v) == 1 for v in xs), "90° kesimde takım X sabit: " + str(xs))
c = [v[0] for v in xs]
check(c == [7, 113, 219], f"kesim merkezleri X0-rt, X0+L+rt, ... : {c}")
check(abs((c[1] - rt) - (c[0] + rt) - 100) < 1e-6 and abs((c[2] - rt) - (c[1] + rt) - 100) < 1e-6, "iki parça da net L = 100")
zmin = {}
for m in mv:
    if m["g"] == 1 and m["grp"] and "kesimi" in m["grp"][1]: a = round(m["pos"]["A"]) % 180; zmin[a] = min(zmin.get(a, 1e9), m["pos"]["Z"])
# yüzey 1/3 (üst/alt): h = B/2 = 15, zofs 15 ; yüzey 2/4: h = A/2 = 30
check(abs(zmin[0] - (-(t + ov))) < 1e-6 and abs(zmin[90] - (30 - t - ov - 15)) < 1e-6, f"derinlik t + taşma: üst {zmin[0]} yan {zmin[90]}")
ysw = [m["pos"]["Y"] for m in mv if m["g"] == 1 and m["grp"] and "kesimi" in m["grp"][1] and round(m["pos"]["A"]) % 180 == 0]
check(min(ysw) <= -(30 + rt) and max(ysw) >= 30 + rt, "takım yüzü kenardan kenara (± A/2 + rt) geçiyor")
order = [m["pos"]["X"] for m in mv if m["g"] == 0 and m["grp"] and "kesimi" in m["grp"][1] and "X" in m["line"]]
check(order == sorted(order), "kesim sırası boru ucundan aynaya (X artan)")
# köşe radyüsü büyük: derinlik otomatik artar
out, msgs, _ = gen(dro({1500: 1, 1502: 40, 1503: 40, 1504: 2, 1505: 6}))
zm = min(m["pos"]["Z"] for m in parse(out) if m["g"] == 1)
exp = -((6 - (6 - 2) * 0.70710678) + ov)
check(abs(zm - round(exp, 3)) < 0.002, f"köşe R6 t2: derinlik {zm} (beklenen {exp:.3f})")

# yuvarlak 45° gönye: her takım noktası açınımda parça kenarından rt uzakta (fire tarafında)
R = 20
def edge_dist(case, front=True):
    out, msgs, _ = gen(case); mv = parse(out)
    pts = [m["pos"] for m in mv if m["g"] == 1 and m["grp"] == (1, "on uc kesimi" if front else "arka uc kesimi") and m["pos"]["Z"] < 0]
    return pts, msgs
case = dro({1506: 45, 1507: 45, 1508: 30, 1510: 1})
pts, msgs = edge_dist(case)
mm = 1.0
curve = [(30 + mm * R * math.cos(math.radians(a / 10)), R * math.radians(a / 10)) for a in range(0, 3600)]
def mind(p):
    s = R * math.radians(p["A"] % 360)
    return min(math.hypot(p["X"] - cx, ((s - cs + math.pi * R) % (2 * math.pi * R)) - math.pi * R) for cx, cs in curve)
ds = [mind(p) for p in pts[::7]]
side = all(p["X"] < 30 + mm * R * math.cos(math.radians(p["A"])) for p in pts)
check(len(ds) > 50 and max(abs(x - rt) for x in ds) < 0.05 and side, f"45° gönye: takım-kenar mesafesi {min(ds):.3f}..{max(ds):.3f} (rt {rt}), takım fire tarafında")
zs = [m["pos"]["Z"] for m in parse(gen(case)[0]) if m["g"] == 1 and m["grp"] == (1, "on uc kesimi")]
check(abs(min(zs) - (-(t + ov))) < 1e-6 and zs[0] > 0, f"yuvarlak: helisel iniş havadan başlıyor (Z {zs[0]}), son tur Z {min(zs)}")
# balık ağzı iki uç: kenar mesafesi
case = dro({1530: 1, 1531: 2, 1532: 50, 1533: 90, 1508: 20, 1510: 1})
pts, msgs = edge_dist(case)
Rb = 25
curve = [(20 - (Rb - math.sqrt(Rb * Rb - (R * math.sin(math.radians(a / 10))) ** 2)), R * math.radians(a / 10)) for a in range(0, 3600)]
ds = [mind(p) for p in pts[::7]]
check(len(ds) > 50 and max(abs(x - rt) for x in ds) < 0.08, f"balık ağzı K50: takım-kenar mesafesi {min(ds):.3f}..{max(ds):.3f}")

print("3) Delikler")
HOLES = [(1, 50, 0, 0, 20, 0, 0),      # yuvarlak Ø20 -> kontur r = 7
         (1, 100, 90, 0, 6, 0, 0),     # Ø6 = takım -> delme
         (3, 150, 0, 4, 30, 12, 0),    # pencere 30×12, Y ofset 4 -> yol 24×6
         (2, 200, 180, 0, 20, 6, 0)]   # oval W = takım -> yiv 14
d = dro({1500: 1, 1502: 60, 1503: 30, 1504: t, 1505: 1, 1508: 10, 1523: 1}, HOLES)
out, msgs, _ = gen(d); mv = parse(out)
def hole(n): return [m for m in mv if m["grp"] == (1, "delik %d" % n)]
h1 = [m["pos"] for m in hole(1) if m["g"] == 1 and m["pos"]["Z"] <= 0.5]
rr = [math.hypot(p["X"] - 60, p["Y"]) for p in h1[1:]]
check(max(abs(r - 7) for r in rr) < 0.01, f"Ø20 delik: takım yolu yarıçapı {min(rr):.3f}..{max(rr):.3f} (beklenen 7), merkez X60")
check(abs(min(p["Z"] for p in h1) - (-(t + ov))) < 1e-6, "delik derinliği t + taşma")
area = sum(a["X"] * b["Y"] - b["X"] * a["Y"] for a, b in zip(h1[1:], h1[2:]))
check(area > 0, "tırmanma: delik konturu saat yönü tersi")
h2 = hole(2)
check(all(m["pos"]["X"] == 110 and m["pos"]["Y"] == 0 for m in h2 if m["g"] == 1) and abs(next(m for m in h2 if m["line"].startswith("G0 A"))["pos"]["A"] % 360 - 90) < 1e-6
      and sum(1 for m in h2 if m["g"] == 0 and m["line"].startswith("G0 Z")) >= 3, "Ø6 = takım: delme, gagalama, yüzey 2 (A90)")
h3 = [m["pos"] for m in hole(3) if m["g"] == 1]
bx = (max(p["X"] for p in h3) - min(p["X"] for p in h3), max(p["Y"] for p in h3) - min(p["Y"] for p in h3), (max(p["Y"] for p in h3) + min(p["Y"] for p in h3)) / 2)
check(abs(bx[0] - 24) < 1e-6 and abs(bx[1] - 6) < 1e-6 and abs(bx[2] - 4) < 1e-6, f"pencere 30×12: yol {bx[0]} × {bx[1]}, Y merkezi {bx[2]}")
h4 = [m["pos"] for m in hole(4) if m["g"] == 1]
check(set(p["Y"] for p in h4) == {0} and abs(max(p["X"] for p in h4) - min(p["X"] for p in h4) - 14) < 1e-6, "oval 20×6 (W = takım): yiv, eksen boyu 14")
out2, *_ = gen({**d, 1524: 1}); mv2 = parse(out2)
h1b = [m["pos"] for m in mv2 if m["grp"] == (1, "delik 1") and m["g"] == 1 and m["pos"]["Z"] <= 0.5]
area = sum(a["X"] * b["Y"] - b["X"] * a["Y"] for a, b in zip(h1b[1:], h1b[2:]))
check(area < 0, "konvansiyonel: delik konturu saat yönü")
# yuvarlak boruda delik: Y ofsette derinlik iç yüzeyin altına iniyor
d = dro({1504: 2, 1508: 10}, [(1, 60, 30, 5, 10, 0, 0)])
out, msgs, _ = gen(d)
zb = min(m["pos"]["Z"] for m in parse(out) if m["grp"] == (1, "delik 1"))
exp = math.sqrt(18 ** 2 - 10 ** 2) - 0.5 - 20
check(abs(zb - round(exp, 3)) < 0.002, f"yuvarlak boru Ø10 delik Y+5: dip Z {zb} (iç yüzey altı {exp:.3f})")

print("4) Güvenlik")
for name, case in {"dikd": dro({1500: 1, 1510: 2}, HOLES[:3]), "yuv_gonye": dro({1506: 60, 1508: 30, 1510: 2}, [(1, 80, 0, 0, 10, 0, 0)])}.items():
    out, msgs, _ = gen(case); mv = parse(out)
    zsafe = max(m["pos"]["Z"] for m in mv)
    bad = [m["line"] for m in mv if m["g"] == 0 and any(k in m["line"] for k in "XYA") and m["prev"]["Z"] < zsafe - 1e-6]
    check(not bad, f"{name}: G0 ile X/Y/A hareketi yalnız güvenli Z'de ({len(bad)})")
    check(all(m["spindle"] for m in mv if m["g"] == 1), f"{name}: her kesim hareketinde iş mili açık")
    check(all(m["F"] for m in mv if m["g"] == 1 and m["gm"] == 93), f"{name}: G93 satırlarının hepsinde F var")
    check(out[-1] == "M30" and "M5" in out[-4:], f"{name}: sonda M5 ve M30")
d = dro({}); vbrun.run(MAC("M900"), d, {}, {}, shared=True)
check(d[1528] > 0 and d[1526] > 300 and d[1527] == 1, f"çıktı DRO: boru boyu {d[1526]}, en küçük X0 {d[1527]}, süre {d[1528]} dk")

print("5) Hatalar ve seçim makroları")
out, msgs, _ = gen(dro({1522: 0.01}))
check(msgs[-1].startswith("Program hazir"), "A segment 0.01: en küçük 0.25'e çekiliyor, dizi taşmıyor")
for kw, holes, want in [({1506: 45}, (), "X0 en az"), ({}, [(1, 50, 0, 0, 4, 0, 0)], "takim capindan"), ({1512: 2}, (), "takim kesme boyundan"),
                        ({1500: 1}, [(1, 50, 0, 18, 10, 0, 0)], "duz kismindan"), ({}, [(1, 50, 0, 15, 10, 0, 0)], "cok genis"),
                        ({1509: 100}, [(1, 98, 0, 0, 10, 0, 0)], "Delik 1 parcanin disinda"), ({1504: 25}, (), "Et kalinligi"),
                        ({1511: 40}, (), "boru capindan"), ({}, [(7, 50, 0, 0, 10, 0, 0)], "tipi gecersiz"), ({1516: 0.01}, (), "Cok fazla nokta")]:
    out, msgs, _ = gen(dro(kw, holes))
    check(not out and want in msgs[-1], f"hata '{want}': {msgs[-1][:60]}")
for m, dn, p, led in [("M902", 1500, 1, 1501), ("M903", 1530, 1, 1504), ("M904", 1531, 2, 1507), ("M905", 1521, 2, 1510), ("M906", 1524, 1, 1512)]:
    st = dro({}); leds = {}
    vbrun.run(MAC(m), st, {}, {}, shared=True, leds_in=leds, param1=p)
    check(st[dn] == p and leds.get(led) == 1, f"{m} P{p}: DRO {dn} = {st[dn]}, LED {led} yanık")

print("\nSONUÇ:", "BAŞARILI" if not fails else f"{len(fails)} HATA")
sys.exit(1 if fails else 0)
