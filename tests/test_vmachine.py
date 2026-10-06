"""Sanal işleme testleri:  python tests/test_vmachine.py   (gereksinim: pip install numpy scipy)
Makronun ürettiği G-kod, makine kinematiğiyle (X boruyu sürer, A döndürür, takım/ışın Y-Z'de) çalıştırılır;
gerçek takım çapında (freze) veya kerf çapında (lazer) malzeme kaldırılır. Sonra çıkan parçalar ölçülür:
  - her parça borudan ayrıldı mı, kaç parça / fire / göbek çıktı
  - parça boyu ve uç kenarları (dış yüzeyde, her çevre noktasında) tasarım eğrisine göre sapma
  - delik ölçüsü ve konumu (parça ön kenarına göre)
  - çarpışma: G0 ile malzemeye değme, takım kesme boyunun üstünde malzeme (şaft / pens)
Izgara 0,05 mm: ölçüm çözünürlüğü ±0,05 mm. Tolerans: TOL.
Açınım resimleri: dist/previews/vm_<durum>.png
"""
import os, sys, math, time
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools")); import vbrun, vmachine as vm
TOL = 0.07          # ölçüm toleransı (ızgara 0,05 + yuvarlama)
fails = []
def check(cond, msg):
    print(("  ok   " if cond else "  HATA ") + msg)
    if not cond: fails.append(msg)
rd = lambda *p: open(os.path.join(ROOT, *p), encoding="utf-8").read()
PAR = {"VelocitiesX": 100, "VelocitiesY": 100, "VelocitiesZ": 50, "VelocitiesA": 60}
os.makedirs(os.path.join(ROOT, "dist", "previews"), exist_ok=True)

LBASE = {1000: 1, 1001: 30, 1002: 40, 1003: 30, 1004: 2, 1005: 2, 1006: 90, 1007: 90, 1008: 30, 1009: 1200, 1010: 0.3, 1011: 0.2,
         1012: 25, 1013: 1, 1014: 800, 1015: 2, 1016: 2, 1017: 60, 1018: 2, 1019: 1, 1022: 0, 1023: 1, 1030: 0, 1031: 0, 1032: 40, 1033: 90, 1039: 1}
MBASE = {}
vbrun.run(rd("mill", "macros", "M901.bas"), MBASE, {}, {}, shared=True)

def laser_case(kw, holes=()):
    d = dict(LBASE); d.update(kw)
    for i, h in enumerate(holes):
        for j, v in enumerate(h): d[1100 + i * 10 + j] = v
    for c in range(7): d[1040 + c] = d.get(1100 + c, 0)
    out, msgs, *_ = vbrun.run(rd("macros", "M800.bas"), d, PAR, {}, shared=True)
    return d, out, msgs

def mill_case(kw, holes=()):
    d = dict(MBASE); d.update(kw)
    for i, h in enumerate(holes):
        for j, v in enumerate(h): d[1600 + i * 10 + j] = v
    out, msgs, *_ = vbrun.run(rd("mill", "macros", "M900.bas"), d, PAR, {}, shared=True)
    return d, out, msgs

def simulate(name, kind, d, out, tool_actual=None, msgs=None):
    if msgs is not None: check(bool(out) and "Program hazir" in msgs[-1], f"[{name}] G-kod üretildi: {msgs[-1][:70]}")
    if kind == "laser":
        prof = vm.Profile(int(d[1000]), D=d[1001], A=d[1002], B=d[1003], R=d[1005], t=d[1004])
        xmax = d[1020] + 10; rad = d[1011] / 2
    else:
        prof = vm.Profile(int(d[1500]), D=d[1501], A=d[1502], B=d[1503], R=d[1505], t=d[1504])
        xmax = d[1526] + 10; rad = (tool_actual if tool_actual else d[1511] + d.get(1529, 0)) / 2
    t0 = time.time()
    m = vm.VMachine(prof, xmax)
    m.run(out, kind, rad, stof=d.get(1013, 0), flute=d.get(1512, 1e9))
    pcs = m.pieces()
    m.image(os.path.join(ROOT, "dist", "previews", "vm_%s.png" % name))
    print(f"  [{name}] {len(out)} satır G-kod, {time.time() - t0:.1f} s, {len(pcs)} parça/fire/göbek")
    return prof, m, pcs

def check_parts(name, prof, m, pcs, n, L, front, rear, x0=None, tol=TOL):
    """n parça; front/rear: (beta, fish, bteta, bcap) uç tanımı; x0: 1. parçanın ön kenarı (referans noktasında)."""
    stock = max(pcs, key=lambda k: pcs[k]["x1"])
    sh = lambda end, e: vm.design_shape(prof, end, beta=e[0], fish=e[1], bteta=(e[2] if len(e) > 2 else 90), bcap=(e[3] if len(e) > 3 else 0))
    sf = sh("on", front); sr = sh("arka", rear)
    full = L / m.dx * prof.ns * prof.K                                # tam parçanın voksel sayısı (yaklaşık)
    labels = []; xs = sorted((v["x0"], k) for k, v in pcs.items() if k != stock and v["cells"] > 0.85 * full)
    check(len(xs) == n, f"{name}: {n} parça borudan ayrıldı (bulunan {len(xs)})")
    for pi, (_, lb) in enumerate(xs[:n]):
        xf, xr = m.edges(lb); ok = ~np.isnan(xf)
        c = float(np.median((xf - sf)[ok]))
        ef = float(np.nanmax(np.abs(xf - (c + sf)))); er = float(np.nanmax(np.abs(xr - (c + L + sr))))
        Lm = float(np.median((xr - sr)[ok] - (xf - sf)[ok]))
        msg = f"{name} parça {pi + 1}: boy {Lm:.3f} (L {L}), ön kenar sapma {ef:.3f}, arka kenar sapma {er:.3f}"
        if pi == 0 and x0 is not None: msg += f", ön kenar X {c:.3f} (X0 {x0})"
        check(abs(Lm - L) <= tol and ef <= tol and er <= tol and (pi > 0 or x0 is None or abs(c - x0) <= tol), msg + f"  [tol {tol:.3f}]")
        labels.append((lb, c))
    return labels

def check_hole(name, m, lb, c, hx, A, hy, L, W, arc=False):
    r = m.hole(lb, c + hx, A, hy, wrap_arc=arc)
    if r is None:
        check(False, f"{name}: delik bulunamadı (X {hx}, A {A})"); return
    lx, ly, cx = r
    check(abs(lx - L) <= TOL and abs(ly - W) <= TOL + 0.05 and abs(cx - c - hx) <= TOL,
          f"{name}: {lx:.3f} × {ly:.3f} (tasarım {L} × {W}), merkez X {cx - c:.3f} (tasarım {hx})")

def check_events(name, m):
    ev = m.events
    check(not ev["rapid_contact"] and not ev["holder_contact"],
          f"{name}: çarpışma yok (G0 malzemede {len(ev['rapid_contact'])}, şaft/pens {len(ev['holder_contact'])})")

def ktol(fpmax, k=0.2):
    """Lazer: kesim çizgisi sabit kerf/2 kaydırılır; eğik kenarda gerçek kayma (k/2)·√(1+eğim²) → fark payı."""
    return TOL + k / 2 * (math.sqrt(1 + fpmax ** 2) - 1)

print("1) Lazer (M800, kerf 0.2, kerf telafili)")
d, out, msgs = laser_case({1000: 0, 1006: 45, 1007: 45, 1017: 80})
prof, m, pcs = simulate("lazer_yuv_gonye45", "laser", d, out, msgs=msgs)
check_parts("lazer yuvarlak 45° (ortak kesim)", prof, m, pcs, 2, 80, (45, False), (45, False), x0=30, tol=ktol(1.0))

HL = [(1, 30, 0, 0, 10, 0, 0), (3, 30, 90, 2, 20, 8, 2)]
d, out, msgs = laser_case({}, HL)
prof, m, pcs = simulate("lazer_dikd_tek_delik", "laser", d, out, msgs=msgs)
lbs = check_parts("lazer dikdörtgen tek seferde 90°", prof, m, pcs, 2, 60, (90, False), (90, False), x0=30)
for lb, c in lbs[:1]:
    check_hole("lazer Ø10 yüzey 1", m, lb, c, 30, 0, 0, 10, 10)
    check_hole("lazer pencere 20×8 yüzey 2 Y+2", m, lb, c, 30, 90, 2, 20, 8)

d, out, msgs = laser_case({1019: 1, 1007: 60})
prof, m, pcs = simulate("lazer_dikd_tek_a1a2", "laser", d, out, msgs=msgs)
check_parts("lazer dikdörtgen tek seferde α 90/60", prof, m, pcs, 2, 60, (90, False), (60, False), x0=30, tol=ktol(1 / math.tan(math.radians(60))))
# bilinen sınır: kenar kenar + eğik uç -> yan yüzde dik ışın eti sabit X'te keser, köşede köprü kalır
d, out, msgs = laser_case({1019: 0, 1007: 60})
prof, m, pcs = simulate("lazer_dikd_kenar_a1a2", "laser", d, out)
stock = max(pcs, key=lambda k: pcs[k]["x1"]); sep = [v for k, v in pcs.items() if k != stock and v["x1"] - v["x0"] > 48]
check("kenar kenar egik" in msgs[-1] and len(sep) < 2, f"kenar kenar α 90/60 (et 2): köşe köprüsü simülasyonda görülüyor (ayrılan {len(sep)}/2) ve M800 uyarıyor")

d, out, msgs = laser_case({1000: 0, 1030: 1, 1031: 2, 1032: 40, 1033: 90, 1017: 80, 1018: 1, 1008: 40}, [(1, 40, 90, 0, 8, 0, 0)])
prof, m, pcs = simulate("lazer_yuv_balik", "laser", d, out, msgs=msgs)
lbs = check_parts("lazer yuvarlak balık ağzı iki uç K40", prof, m, pcs, 1, 80, (90, True, 90, 40), (90, True, 90, 40), tol=ktol(15 / math.sqrt(400 - 225)))
for lb, c in lbs[:1]: check_hole("lazer yuvarlak Ø8 A90 (çevreye sarılı)", m, lb, c, 40, 90, 0, 8, 8, arc=True)

print("2) Freze (M900, takım Ø6)")
d, out, msgs = mill_case({1500: 0, 1501: 30, 1509: 60, 1510: 2, 1508: 10}, [(1, 30, 0, 0, 10, 0, 0), (1, 45, 90, 0, 6, 0, 0)])
prof, m, pcs = simulate("freze_yuv_90_delik", "mill", d, out, msgs=msgs)
lbs = check_parts("freze yuvarlak 90°", prof, m, pcs, 2, 60, (90, False), (90, False), x0=10)
check_events("freze yuvarlak 90°", m)
for lb, c in lbs[:1]:
    check_hole("freze yuvarlak Ø10 A0 (dik izdüşüm)", m, lb, c, 30, 0, 0, 10, 10)
    check_hole("freze yuvarlak Ø6 delme A90", m, lb, c, 45, 90, 0, 6, 6)

HM = [(3, 40, 0, 3, 20, 8, 0), (2, 40, 90, 0, 16, 6, 0), (1, 30, 180, 0, 8, 0, 0)]
d, out, msgs = mill_case({1500: 1, 1502: 40, 1503: 30, 1505: 1, 1506: 45, 1507: 45, 1509: 80, 1510: 2, 1508: 30}, HM)
prof, m, pcs = simulate("freze_dikd_45_delik", "mill", d, out, msgs=msgs)
# dik takım: yan yüzde eğik düzlem basamakla izlenir; dış yüzey kenarı ilk ince pasoyla (0,05) -> sapma ≤ cot(α)·0,05
lbs = check_parts("freze dikdörtgen 45° (yüzey kenarı)", prof, m, pcs, 2, 80, (45, False), (45, False), x0=30, tol=TOL + 0.05)
check_events("freze dikdörtgen 45°", m)
for lb, c in lbs[:1]:
    check_hole("freze pencere 20×8 yüzey 1 Y+3", m, lb, c, 40, 0, 3, 20, 8)
    check_hole("freze yiv 16×6 yüzey 2", m, lb, c, 40, 90, 0, 16, 6)
    check_hole("freze Ø8 yüzey 3", m, lb, c, 30, 180, 0, 8, 8)

d, out, msgs = mill_case({1500: 0, 1501: 30, 1530: 1, 1531: 2, 1532: 40, 1533: 75, 1509: 80, 1510: 1, 1508: 30})
prof, m, pcs = simulate("freze_yuv_balik", "mill", d, out, msgs=msgs)
check_parts("freze yuvarlak balık ağzı iki uç K40 θ75", prof, m, pcs, 1, 80, (90, True, 75, 40), (90, True, 75, 40))
check_events("freze balık ağzı", m)

d, out, msgs = mill_case({1500: 1, 1502: 40, 1503: 30, 1529: -0.1, 1525: 0.3, 1509: 60, 1510: 1, 1508: 10}, [(1, 30, 0, 0, 12, 0, 0)])
prof, m, pcs = simulate("freze_duzeltme_bitirme", "mill", d, out, tool_actual=5.9, msgs=msgs)
lbs = check_parts("freze takım Ø5.9 (düzeltme −0.1), bitirme payı 0.3", prof, m, pcs, 1, 60, (90, False), (90, False), x0=10)
for lb, c in lbs[:1]: check_hole("freze Ø12 bitirme pasosuyla", m, lb, c, 30, 0, 0, 12, 12)

d, out, msgs = mill_case({1500: 1, 1502: 40, 1503: 30, 1509: 60, 1510: 1, 1508: 10}, [(1, 30, 0, 0, 12, 0, 0)])
prof, m, pcs = simulate("freze_takim_hatali", "mill", d, out, tool_actual=6.1)
xf, xr = m.edges(m.part_at(40)); Lm = float(np.nanmedian(xr - xf)); r = m.hole(m.part_at(40), 40, 0, 0)
check(abs(Lm - 59.9) <= TOL and r and abs(r[0] - 12.1) <= TOL,
      f"düzeltme girilmezse (gerçek takım Ø6.1): parça {Lm:.3f} (−0.1), delik {r[0] if r else 0:.3f} (+0.1) - simülasyon farkı görüyor")

print("\nSONUÇ:", "BAŞARILI" if not fails else f"{len(fails)} HATA")
sys.exit(1 if fails else 0)
