"""Sanal işleme (virtual machining): G-kodu makine kinematiğiyle çalıştırır, boru etinden malzeme kaldırır,
çıkan parçaları ölçer ve tasarımla karşılaştırır.  Gereksinim: numpy, scipy.

Model (makineyle aynı):
  - Kafa X'te sabit. Makine X = borunun kafanın altındaki noktası (X0 = boru ön ucu).
  - A: boru döner. Makine (y, z) -> boru (u, v):  u = y·cosA + zc·sinA,  v = -y·sinA + zc·cosA  (zc = z + zofs, merkez tabanlı)
  - Mach3 bütün eksenleri doğrusal enterpole eder (G1 X Y Z A); simülasyon da hareketi eksen uzayında doğrusal örnekler.
  - Freze: düz uçlu silindir (çap = gerçek takım çapı), eksen makine Z'si. İş mili açıkken her hareket keser.
    Takım kesme boyunun üstünde malzemeye değme = şaft/pens çarpışması. G0 ile malzeme kaldırma = çarpışma.
  - Lazer: kerf çapında ışın, lazer açıkken (M3..M5) her harekette yakın eti boydan boya keser.
Boru eti: X'te ve çevrede dx (varsayılan 0,05 mm) hücreler, et kalınlığında K katman (dış yüzey = katman 0).
"""
import math, re
import numpy as np
from scipy import ndimage

D2R = math.pi / 180


# ---------------------------------------------------------------- profil
class Profile:
    """Dış yüzey çevresi: hücre merkezleri (u, v), dış normal (nu, nv), katman noktaları. s = 0 üst yüz ortası, +u yönüne."""
    def __init__(self, tip, D=0, A=0, B=0, R=0, t=2, ds=0.05, K=5):
        self.tip, self.t, self.K = tip, t, K
        if tip == 0:
            self.a = self.b = self.r = D / 2
            P = 2 * math.pi * self.a; n = int(round(P / ds)); phi = (np.arange(n) + 0.5) / n * 2 * math.pi
            u, v = self.a * np.sin(phi), self.a * np.cos(phi); nu, nv = np.sin(phi), np.cos(phi)
        else:
            a, b = A / 2, B / 2; r = max(0.0, min(R, a, b)); self.a, self.b, self.r = a, b, r
            segs = [("L", (0, b), (a - r, b), (0, 1)), ("C", (a - r, b - r), 90, 0), ("L", (a, b - r), (a, -(b - r)), (1, 0)),
                    ("C", (a - r, -(b - r)), 0, -90), ("L", (a - r, -b), (-(a - r), -b), (0, -1)), ("C", (-(a - r), -(b - r)), -90, -180),
                    ("L", (-a, -(b - r)), (-a, b - r), (-1, 0)), ("C", (-(a - r), b - r), 180, 90), ("L", (-(a - r), b), (0, b), (0, 1))]
            lens = [math.dist(g[1], g[2]) if g[0] == "L" else abs(g[3] - g[2]) * D2R * r for g in segs]
            P = sum(lens); n = int(round(P / ds)); sc = (np.arange(n) + 0.5) / n * P
            u = np.zeros(n); v = np.zeros(n); nu = np.zeros(n); nv = np.zeros(n); s0 = 0
            for g, L in zip(segs, lens):
                m = (sc >= s0) & (sc < s0 + L) if L > 0 else np.zeros(n, bool); k = (sc[m] - s0) / max(L, 1e-12)
                if g[0] == "L":
                    u[m] = g[1][0] + (g[2][0] - g[1][0]) * k; v[m] = g[1][1] + (g[2][1] - g[1][1]) * k; nu[m], nv[m] = g[3]
                else:
                    an = (g[2] + (g[3] - g[2]) * k) * D2R
                    u[m] = g[1][0] + r * np.cos(an); v[m] = g[1][1] + r * np.sin(an); nu[m] = np.cos(an); nv[m] = np.sin(an)
                s0 += L
        self.P, self.ns, self.ds = P, n, P / n
        self.u, self.v, self.nu, self.nv = u, v, nu, nv
        dep = np.linspace(0, t, K)                                     # katman derinlikleri (0 = dış yüzey, t = iç yüzey)
        self.qu = u[:, None] - dep[None, :] * nu[:, None]              # (ns, K)
        self.qv = v[:, None] - dep[None, :] * nv[:, None]
        self.zofs = self.a if tip == 0 else self.b

    def at_machine(self, Adeg):
        """Her dış yüzey hücresinin A açısındaki makine (y, zc) konumu."""
        A = Adeg * D2R; c, s = math.cos(A), math.sin(A)
        return self.u * c - self.v * s, self.u * s + self.v * c


# ---------------------------------------------------------------- G-kod
def parse_gcode(lines):
    """[(g, on, (x,y,z,a) başlangıç, (x,y,z,a) bitiş, satır)]  g = 0 / 1;  on = iş mili veya lazer açık."""
    pos = [0.0, 0.0, 0.0, 0.0]; mode = 0; on = False; out = []
    for li, raw in enumerate(lines, 1):
        l = re.sub(r"\(.*?\)", "", str(raw)).upper().strip()
        if not l: continue
        tgt = list(pos); has = False
        for c, val in re.findall(r"([A-Z])\s*([-+]?(?:\d+\.?\d*|\.\d+))", l):
            v = float(val)
            if c == "G" and v in (0, 1): mode = int(v)
            elif c == "M" and v in (3, 4): on = True
            elif c == "M" and v in (5, 30, 2): on = False
            elif c in "XYZA": tgt["XYZA".index(c)] = v; has = True
        if has:
            out.append((mode, on, tuple(pos), tuple(tgt), li)); pos = tgt
    return out


# ---------------------------------------------------------------- işleme
class VMachine:
    def __init__(self, prof, xmax, dx=0.05, xmin=0.0):
        self.p = prof; self.dx = dx; self.xmin = xmin
        self.nx = int(math.ceil((xmax - xmin) / dx)); self.xc = xmin + (np.arange(self.nx) + 0.5) * dx
        self.rem = np.zeros((self.nx, prof.ns, prof.K), bool)          # kaldırılmış hücreler
        self.events = {"rapid_contact": [], "holder_contact": []}

    def run(self, lines, kind, rad, stof=0.0, flute=1e9, step=None):
        """kind 'mill' (rad = takım yarıçapı, flute = kesme boyu) veya 'laser' (rad = kerf/2, stof = nozul yüksekliği)."""
        p = self.p; step = step or (0.1 if kind == "mill" else 0.02)
        Rm = max(p.a, p.b)
        for g, on, a0, a1, li in parse_gcode(lines):
            if not on: continue
            d = [a1[i] - a0[i] for i in range(4)]
            L = max(abs(d[0]), abs(d[1]), abs(d[2]), abs(d[3]) * D2R * Rm)
            n = max(1, int(math.ceil(L / step)))
            for k in range(0 if g == 1 else 1, n + 1):
                f = k / n
                self._stamp(*(a0[i] + d[i] * f for i in range(4)), kind, rad, stof, flute, g, li)

    def _stamp(self, X, y, z, Adeg, kind, rad, stof, flute, g, li):
        p = self.p; A = Adeg * D2R; c, s = math.cos(A), math.sin(A)
        zc = z + p.zofs
        tu, tv = y * c + zc * s, -y * s + zc * c                          # takım ucu / nozul (boru çerçevesi)
        du, dv = p.qu - tu, p.qv - tv
        along = du * s + dv * c                                         # takım ekseni boyunca (yukarı +)
        perp = du * c - dv * s                                          # makine Y yönünde
        if kind == "mill": cond = (along >= -1e-9) & (np.abs(perp) < rad)
        else: cond = (along <= 0.05) & (along >= -(stof + p.t + (p.r if p.tip else 0) + 1.0)) & (np.abs(perp) < rad)   # yakın et (köşe yayı dahil)
        si, li_ = np.nonzero(cond)
        if not si.size: return
        hx = np.sqrt(rad * rad - perp[si, li_] ** 2)
        i0 = max(0, int((X - rad - self.xmin) / self.dx) - 1); i1 = min(self.nx, int((X + rad - self.xmin) / self.dx) + 2)
        if i0 >= i1: return
        xs = self.xc[i0:i1]
        m = np.abs(xs[:, None] - X) <= hx[None, :]                       # (w, nc)
        sub = self.rem[i0:i1, si, li_]
        new = m & ~sub
        if new.any():
            if g == 0: self.events["rapid_contact"].append((li, X, y, z, Adeg))
            if kind == "mill":
                hi = (along[si, li_] > flute)[None, :] & new
                if hi.any(): self.events["holder_contact"].append((li, X, y, z, Adeg))
        self.rem[i0:i1, si, li_] = sub | m

    # ------------------------------------------------------------ analiz
    def pieces(self):
        """Malzeme vokselleri (x, s, katman) 6-komşulukla bağlı parçalar (3B: eğik kesimde katmanlar arası geçiş doğru).
        Her katman 2B etiketlenir, sonra komşu katmanlar ve çevre dikişi (s = 0 / ns-1) birleştirilir.
        self.lab: dış yüzey (katman 0) hücrelerinin parça etiketi (malzeme yoksa 0)."""
        K = self.p.K; labs = []; off = 0
        for k in range(K):
            l, n = ndimage.label(~self.rem[:, :, k])
            labs.append(np.where(l > 0, l + off, 0)); off += n
        par = np.arange(off + 1)
        def find(a):
            r = a
            while par[r] != r: r = par[r]
            while par[a] != r: par[a], a = r, par[a]
            return r
        pairs = []
        for k in range(K):
            a, b = labs[k][:, 0], labs[k][:, -1]; m = (a > 0) & (b > 0); pairs.append(np.stack([a[m], b[m]], 1))
            if k + 1 < K:
                a, b = labs[k], labs[k + 1]; m = (a > 0) & (b > 0); pairs.append(np.stack([a[m], b[m]], 1))
        for a, b in np.unique(np.concatenate(pairs), axis=0):
            ra, rb = find(int(a)), find(int(b))
            if ra != rb: par[ra] = rb
        roots = np.array([find(i) for i in range(off + 1)])
        self.lab = roots[labs[0]]
        out = {}
        for k in range(K):
            lk = roots[labs[k]]
            for r in np.unique(lk):
                if r == 0: continue
                xs = np.nonzero((lk == r).any(axis=1))[0]
                o = out.setdefault(int(r), dict(x0=1e18, x1=-1e18, cells=0))
                o["x0"] = min(o["x0"], self.xmin + xs[0] * self.dx); o["x1"] = max(o["x1"], self.xmin + (xs[-1] + 1) * self.dx)
                o["cells"] += int((lk == r).sum())
        return out

    def part_at(self, x):
        """x konumundaki katı parçanın etiketi (o X sütununda en çok hücresi olan)."""
        i = int((x - self.xmin) / self.dx); col = self.lab[i]; col = col[col > 0]
        return int(np.bincount(col).argmax()) if col.size else 0

    def edges(self, label):
        """Parçanın dış yüzeyde her çevre sütunundaki ön / arka kenar X'i (hücre sınırı)."""
        outer = (self.lab == label) & ~self.rem[:, :, 0]
        has = outer.any(axis=0)
        i0 = np.argmax(outer, axis=0); i1 = self.nx - 1 - np.argmax(outer[::-1], axis=0)
        xf = self.xmin + i0 * self.dx; xr = self.xmin + (i1 + 1) * self.dx
        return np.where(has, xf, np.nan), np.where(has, xr, np.nan)

    def hole(self, label, xc, Adeg, y, wrap_arc=False):
        """Parça içindeki deliği ölç: merkezden (x, A açısında makine y) taşkın doldurma.
        Dönüş: (X boyu, Y boyu) – Y, A açısındaki makine y'si (dik izdüşüm) veya wrap_arc=True ise dış çevre yay boyu."""
        p = self.p; part_outer = (self.lab == label) & ~self.rem[:, :, 0]
        ym, zm = p.at_machine(Adeg)
        top = zm > 0
        if wrap_arc: si = int(np.argmax(np.where(top, zm, -1e9)))      # yay: A açısında en üst nokta, y ayrıca yay boyu
        else: si = int(np.argmin(np.where(top, np.abs(ym - y), 1e9)))
        shift = p.ns // 2 - si
        po = np.roll(part_outer, shift, axis=1)
        i = int((xc - self.xmin) / self.dx)
        free = ~po
        lab, _ = ndimage.label(free)
        L = lab[i, p.ns // 2]
        if L == 0: return None
        reg = lab == L
        if reg[:, 0].any() or reg[:, -1].any() or reg[0].any() or reg[-1].any(): return None   # dışarıya açık: delik değil
        xs = np.nonzero(reg.any(axis=1))[0]; ss = np.nonzero(reg.any(axis=0))[0]
        lx = (xs[-1] - xs[0] + 1) * self.dx
        if wrap_arc: ly = (ss[-1] - ss[0] + 1) * p.ds
        else:
            yy = np.roll(ym, shift)[ss]
            ly = yy.max() - yy.min() + p.ds * abs(np.cos(0))                  # hücre genişliği kadar sınır payı
        cx = self.xmin + (xs[0] + xs[-1] + 1) / 2 * self.dx
        return lx, ly, cx

    def image(self, path, scale=4):
        """Açınım resmi (dış yüzey): gri = malzeme, renkli = parçalar, siyah = kesilmiş."""
        from PIL import Image
        lab = self.lab; outer = ~self.rem[:, :, 0]
        rng = np.random.default_rng(1); cols = rng.integers(70, 230, (lab.max() + 1, 3)).astype(np.uint8)
        img = np.where(outer[..., None], cols[lab], np.uint8(20)).astype(np.uint8)
        img = img.transpose(1, 0, 2)[::-1]                              # yatay X, düşey çevre
        im = Image.fromarray(img)
        im = im.resize((max(1, im.width // scale), max(1, im.height // scale)), Image.NEAREST)
        im.save(path)


# ---------------------------------------------------------------- tasarım (kenar eğrileri)
def design_shape(prof, end, beta, bteta=90, bcap=0, fish=False):
    """Parça ucunun tasarım eğrisi (xref'e göre), her dış yüzey sütunu için. end: 'on' (boru ucu yönü) / 'arka'."""
    u, v = prof.u, prof.v
    w, nn = (v, u) if prof.tip == 0 else (u, v)                        # w eğim koordinatı, n diğer
    if not fish:
        m = 0 if beta >= 89.999 else 1 / math.tan(beta * D2R)
        return m * w
    Rb = bcap / 2; mb = 0 if bteta >= 89.999 else 1 / math.tan(bteta * D2R); sb = math.sin(bteta * D2R)
    sg = -1 if end == "on" else 1
    return w * mb + sg * (Rb - np.sqrt(np.maximum(Rb * Rb - nn * nn, 0))) / sb
