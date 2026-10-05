"""TubeMill wizard ekran çizim yardımcıları (gen_page1.py / gen_page2.py ortak).
Mantıksal alan 1024×768 (Mach3 koordinatları), arka plan BMP 1920×1080 çizilir (Px ölçekler)."""
import os, csv, math
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 768
TW, TH = 1920, 1080
SX, SY = TW / W, TH / H
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vendor", "fonts") + os.sep

# ISA-101 tarzı gri HMI paleti (TubeCutting ile aynı)
BG = (200, 205, 210); PANEL = (226, 229, 232); EDGE = (150, 157, 164); TXT = (31, 42, 51); SUB = (92, 102, 112)
FIELD = (255, 255, 255); RO = (208, 213, 218); BTN = (238, 240, 242); BTNE = (120, 128, 136)
PRI = (47, 93, 138); DRAW = (40, 70, 100); DIM = (150, 80, 20); TOOL = (170, 60, 30)

def f(sz, b=False):
    return ImageFont.truetype(FONTS + ("DejaVuSansCondensed-Bold.ttf" if b else "DejaVuSansCondensed.ttf"), round(sz * SY))

class Px:
    def __init__(s, d): s.d = d
    def _b(s, b): return [b[0] * SX, b[1] * SY, b[2] * SX, b[3] * SY]
    def _p(s, ps): return [(p[0] * SX, p[1] * SY) for p in ps]
    def _k(s, k): k = dict(k); k["width"] = max(1, round(k.get("width", 1) * SY)); return k
    def rectangle(s, b, **k): s.d.rectangle(s._b(b), **s._k(k))
    def ellipse(s, b, **k): s.d.ellipse(s._b(b), **s._k(k))
    def line(s, ps, **k): s.d.line(s._p(ps), **s._k(k))
    def polygon(s, ps, **k): s.d.polygon(s._p(ps), **k)
    def text(s, xy, t, **k): s.d.text((xy[0] * SX, xy[1] * SY), t, **k)
    def textlength(s, t, font): return s.d.textlength(t, font=font) / SX

class Page:
    """Bir wizard sayfası: arka plan resmi + kontrol listesi (CSV)."""
    def __init__(self, title, subtitle):
        self.img = Image.new("RGB", (TW, TH), BG); self.d = Px(ImageDraw.Draw(self.img)); self.ctrls = []
        d = self.d
        d.rectangle([0, 0, W, 48], fill=(58, 72, 86))
        d.text((16, 11), title, font=f(22, True), fill=(240, 242, 244))
        d.text((16 + d.textlength(title, f(22, True)) + 12, 16), "·  " + subtitle, font=f(16), fill=(200, 208, 216))
        d.text((W - 300, 17), "Mach3 · A ekseni · freze iş mili", font=f(13), fill=(190, 198, 206))

    # --- kontroller (CSV satırı: tip, etiket, x, y, w, h, mach3, not, fmt)
    def dro(self, n, x, y, w=100, h=28, ro=False, fmt="%4.3f", note=""):
        self.ctrls.append(("DRO", n, x, y, w, h, "OEM/User DRO %d" % n, ("salt-okunur " if ro else "") + note, fmt))
    def led(self, n, x, y, note=""):
        self.ctrls.append(("LED", "", x, y, 14, 14, "User LED %d" % n, note, ""))

    # --- çizim + kontrol
    def panel(self, x, y, w, h, title):
        d = self.d
        d.rectangle([x, y, x + w, y + h], fill=PANEL, outline=EDGE)
        d.rectangle([x, y, x + w, y + 30], fill=(212, 216, 220), outline=EDGE)
        d.text((x + 12, y + 6), title, font=f(16, True), fill=TXT)

    def row(self, x, y, label, n, unit, ro=False, fmt="%4.3f", note="", lw=150):
        d = self.d
        d.text((x, y + 5), label, font=f(14), fill=TXT)
        bx = x + lw
        d.rectangle([bx, y, bx + 100, y + 28], fill=RO if ro else FIELD, outline=EDGE)
        d.text((bx + 106, y + 6), unit, font=f(13), fill=SUB)
        self.dro(n, bx, y, ro=ro, fmt=fmt, note=note)

    def button(self, x, y, w, h, t, g, primary=False, note=""):
        d = self.d
        d.rectangle([x + 2, y + 2, x + w + 2, y + h + 2], fill=(170, 176, 182))
        d.rectangle([x, y, x + w, y + h], fill=PRI if primary else BTN, outline=BTNE)
        fn = f(17 if primary else 14, True); tw = d.textlength(t, font=fn)
        d.text((x + (w - tw) / 2, y + (h - 18) / 2), t, font=fn, fill=(255, 255, 255) if primary else TXT)
        self.ctrls.append(("BUTON", t, x, y, w, h, g, note, ""))

    def ledsock(self, x, y, n, note=""):
        self.d.rectangle([x - 3, y - 3, x + 17, y + 17], fill=(170, 176, 182), outline=EDGE); self.led(n, x, y, note)

    def note(self, x, y, w, lines, h=None):
        h = h or 10 + 18 * len(lines)
        self.d.rectangle([x, y, x + w, y + h], fill=(236, 238, 240), outline=EDGE)
        for i, t in enumerate(lines): self.d.text((x + 10, y + 6 + i * 18), t, font=f(12), fill=SUB)

    def dimline(self, p1, p2, label, off=(0, 0)):
        d = self.d
        d.line([p1, p2], fill=DIM, width=1)
        for p, q in ((p1, p2), (p2, p1)):
            ang = math.atan2(q[1] - p[1], q[0] - p[0])
            for s in (0.45, -0.45):
                d.line([p, (p[0] + 7 * math.cos(ang + s), p[1] + 7 * math.sin(ang + s))], fill=DIM, width=1)
        d.text(((p1[0] + p2[0]) / 2 + off[0], (p1[1] + p2[1]) / 2 + off[1]), label, font=f(12, True), fill=DIM)

    def status(self):
        self.d.rectangle([10, 668, 1014, 694], fill=(244, 246, 247), outline=EDGE)
        self.ctrls.append(("LABEL", "", 14, 671, 996, 20, "Status (durum satırı)", "Message() buraya yazar", ""))

    def save(self, bmp, png, csvname):
        self.img.save(bmp); self.img.save(png)
        with open(csvname, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh, delimiter=";"); w.writerow(["Tip", "Etiket", "X", "Y", "W", "H", "Mach3 / G-kod", "Not", "Fmt"])
            for c in self.ctrls: w.writerow(c)
        print(csvname, len(self.ctrls), "kontrol")
