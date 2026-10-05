"""TubeMill sayfa 2: uç şekli + delik tablosu (8 delik, DRO 1600 + no*10 + sütun).
Çıktı: tubemill_sayfa2.bmp, tubemill_sayfa2.png, yerlesim_mill2.csv"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui import *

pg = Page("Boru freze sihirbazı", "Uç şekli ve delikler")
d = pg.d

# ---- Sol: uç şekli ----
pg.panel(10, 58, 326, 600, "Uç şekli")
pg.button(22, 98, 120, 34, "Gönye", "M903 P0"); pg.ledsock(150, 108, 1503, "gönye")
pg.button(176, 98, 120, 34, "Balık ağzı", "M903 P1"); pg.ledsock(304, 108, 1504, "balık ağzı")
d.text((22, 146), "Balık ağzı hangi uca", font=f(14, True), fill=TXT)
pg.button(22, 168, 76, 30, "Uç yönü", "M904 P0"); pg.ledsock(104, 176, 1505, "ön uç")
pg.button(124, 168, 76, 30, "Ayna yönü", "M904 P1"); pg.ledsock(206, 176, 1506, "arka uç")
pg.button(226, 168, 76, 30, "İki uç", "M904 P2"); pg.ledsock(308, 176, 1507, "iki uç")
pg.row(22, 214, "Karşı boru  Ø K", 1532, "mm")
pg.row(22, 248, "Birleşim açısı  θ", 1533, "°", fmt="%4.2f")
# kroki: balık ağzı (yandan)
d.rectangle([22, 290, 324, 440], fill=(244, 246, 247), outline=EDGE)
kk = SY / SX; cxp, cyp, Rp, rt = 258, 365, 52, 26
d.ellipse([cxp - Rp * kk, cyp - Rp, cxp + Rp * kk, cyp + Rp], outline=DRAW, width=2, fill=(232, 235, 238))
pts = [(40, cyp - rt)] + [(cxp - math.sqrt(max(Rp * Rp - (yy - cyp) ** 2, 0)) * kk, yy) for yy in [cyp - rt + 2 * rt * i / 40 for i in range(41)]] + [(40, cyp + rt)]
d.polygon(pts, outline=DRAW, fill=(255, 255, 255))
d.text((52, cyp - 8), "parça", font=f(12), fill=SUB)
d.text((cxp - 16, cyp - 8), "karşı", font=f(11), fill=SUB)
d.text((30, 296), "θ = 90°: dik T birleşim", font=f(11), fill=SUB)
pg.note(22, 452, 302, ["Balık ağzında ve α ≠ 90° gönyede her parçanın", "iki ucu ayrı kesilir; araya fire girer.", "",
                        "Dik takım, eğik kenarı izler: çok dik balık", "ağzında (K ≈ boru çapı) kenar eğimi sınırlanır", "(en çok 3:1); kenarı kontrol edin.", "",
                        "Kesimin et içindeki yüzü radyaldir", "(lazer gibi). Kalın ette gönye yüzü eğik", "değil, kademelidir."], h=196)

# ---- Sağ: delik tablosu ----
pg.panel(346, 58, 668, 600, "Delikler (her parçada aynı)")
cols = [("Tip", "%1.0f"), ("X", "%4.2f"), ("A / yüzey °", "%4.1f"), ("Y ofset", "%4.2f"), ("L / Ø", "%4.2f"), ("W", "%4.2f"), ("R", "%4.2f")]
X0c, CW = 392, 88
for c, (t, _) in enumerate(cols):
    tw = d.textlength(t, f(13, True)); d.text((X0c + c * CW + (82 - tw) / 2, 98), t, font=f(13, True), fill=TXT)
for i in range(8):
    y = 122 + i * 34
    d.text((360, y + 5), str(i + 1), font=f(14, True), fill=TXT)
    for c, (_, fmt) in enumerate(cols):
        x = X0c + c * CW
        d.rectangle([x, y, x + 82, y + 26], fill=FIELD, outline=EDGE)
        pg.dro(1600 + i * 10 + c, x, y, w=82, h=26, fmt=fmt, note="delik %d sütun %d" % (i + 1, c))

# lejant: tip simgeleri
ly = 404
d.text((358, ly), "Tip", font=f(14, True), fill=TXT)
icons = [(0, "yok"), (1, "yuvarlak (Ø = L)"), (2, "oval / yiv (L × W)"), (3, "pencere (L × W, R)")]
for k, (n, t) in enumerate(icons):
    x = 358 + k * 160; yy = ly + 24
    d.text((x, yy), "%d" % n, font=f(14, True), fill=PRI)
    if n == 1: d.ellipse([x + 18, yy, x + 18 + 20 * kk, yy + 20], outline=DRAW, width=2)
    if n == 2:
        d.rectangle([x + 28, yy + 4, x + 44, yy + 16], outline=DRAW, width=2)
        d.ellipse([x + 18, yy + 4, x + 18 + 12 * kk, yy + 16], outline=DRAW, width=2); d.ellipse([x + 54 - 12 * kk, yy + 4, x + 54, yy + 16], outline=DRAW, width=2)
    if n == 3: d.rectangle([x + 18, yy + 2, x + 50, yy + 18], outline=DRAW, width=2)
    d.text((x + (60 if n else 18), yy + 2), t, font=f(12), fill=SUB)
pg.note(358, 460, 644, [
    "X: parça ön kenarından delik merkezine.   L: X yönü (boy), W: Y yönü (en).",
    "A: yuvarlakta açı (°). Dikdörtgende yüzey: 0 = Yüzey 1 (üst), 90 = Yüzey 2, 180 = Yüzey 3, 270 = Yüzey 4.",
    "Y ofset: yanal kaydırma (yuvarlakta delik dik izdüşümdür, matkap tezgâhı gibi).",
    "Delik ölçüsü takım çapından küçük olamaz.  Ø = takım Ø  →  delme (gagalama ile).",
    "Oval W = takım Ø  →  yiv (takım eksen boyunca git-gel).  Büyük delik: kontur, rampa ile iner.",
    "Pencere köşesi en az takım yarıçapı kadar yuvarlak kalır (R < takım Ø/2 ise).",
    "Takım yolu ölçüye göre içe kaydırılır (G41/G42 kullanılmaz).  Kesilen göbek düşer:",
    "küçük delikte sorun yok, büyük pencerede göbeği bant veya mıknatısla tutun."], h=158)

pg.status()
pg.button(10, 706, 180, 48, "<< Ana sayfa", "OEM:1", note="1. sayfaya git")
pg.button(706, 706, 154, 48, "Kod üret", "M900", primary=True)
pg.button(870, 706, 144, 48, "Çıkış", "EXIT", note="kaydet + wizard'dan çık")
pg.save("tubemill_sayfa2.bmp", "tubemill_sayfa2.png", "yerlesim_mill2.csv")
