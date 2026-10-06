"""TubeMill sayfa 1: profil, parça, takım ve proses.  Çıktı: tubemill_bg.bmp, tubemill_onizleme.png, yerlesim_mill1.csv"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui import *

pg = Page("Boru freze sihirbazı", "Profil, parça ve takım")
d = pg.d

# ---- Sol: profil ve parça ----
pg.panel(10, 58, 326, 600, "Profil ve parça")
pg.button(22, 98, 120, 34, "Yuvarlak", "M902 P0"); pg.ledsock(150, 108, 1500, "yuvarlak seçili")
pg.button(176, 98, 120, 34, "Dikdörtgen", "M902 P1"); pg.ledsock(304, 108, 1501, "dikdörtgen seçili")
y = 144
for lab, n, u, fmt in [("Çap  D", 1501, "mm", "%4.3f"), ("En  A (yatay)", 1502, "mm", "%4.3f"), ("Boy  B (düşey)", 1503, "mm", "%4.3f"),
                       ("Et kalınlığı  t", 1504, "mm", "%4.3f"), ("Köşe radyüsü  R", 1505, "mm", "%4.3f"),
                       ("Başlangıç açısı  α1", 1506, "°", "%4.2f"), ("Bitiş açısı  α2", 1507, "°", "%4.2f"),
                       ("X0 (ön kenar)", 1508, "mm", "%4.3f"), ("Parça boyu  L", 1509, "mm", "%4.3f"), ("Adet", 1510, "", "%4.0f")]:
    pg.row(22, y, lab, n, u, fmt=fmt); y += 34
pg.ledsock(312, 388, 1502, "X0 çok küçük")

# kroki: boru, iki kesim izi (takım çapı), L net ölçü
kx, ky = 26, 492
d.rectangle([22, 484, 324, 650], fill=(244, 246, 247), outline=EDGE)
d.rectangle([40, 530, 310, 566], fill=(232, 235, 238), outline=DRAW, width=2)
for cx in (92, 250):
    d.rectangle([cx - 8, 520, cx + 8, 576], fill=(255, 220, 200), outline=TOOL, width=1)
    d.rectangle([cx - 6, 494, cx + 6, 528], fill=(190, 196, 202), outline=DRAW)
d.text((40, 572), "boru ucu", font=f(11), fill=SUB)
d.text((60, 506), "takım", font=f(11), fill=SUB)
pg.dimline((100, 590), (242, 590), "L (net)", (-18, 3))
pg.dimline((40, 618), (100, 618), "X0", (-8, 3))
d.text((112, 610), "kesim izi = takım Ø", font=f(11, True), fill=TOOL)
d.text((112, 626), "α ≠ 90° / balık ağzı: uçlar ayrı, araya fire", font=f(11), fill=SUB)

# ---- Orta: takım ve proses ----
pg.panel(346, 58, 330, 600, "Takım ve proses")
y = 96
for lab, n, u, fmt in [("Takım çapı  Ø", 1511, "mm", "%4.3f"), ("Çap düzeltmesi (±)", 1529, "mm", "%4.3f"), ("Kesme boyu", 1512, "mm", "%4.3f"), ("Devir  S", 1513, "dev/dk", "%5.0f"),
                       ("İlerleme  F", 1514, "mm/dk", "%4.0f"), ("Dalma ilerlemesi", 1515, "mm/dk", "%4.0f"), ("Paso derinliği  ap", 1516, "mm", "%4.3f"),
                       ("Taşma (et altı)", 1517, "mm", "%4.3f"), ("Delinmede F", 1518, "%", "%3.0f"), ("Güvenli mesafe", 1519, "mm", "%4.3f"),
                       ("İş mili bekleme", 1520, "s", "%4.1f"), ("A segment açısı", 1522, "°", "%4.2f"), ("Gagalama (0 yok)", 1523, "mm", "%4.3f"),
                       ("Delik bitirme payı", 1525, "mm", "%4.3f")]:
    pg.row(358, y, lab, n, u, fmt=fmt); y += 33
d.text((358, 562), "Soğutma", font=f(14, True), fill=TXT)
pg.button(358, 582, 80, 30, "Yok", "M905 P0"); pg.ledsock(444, 590, 1508, "soğutma yok")
pg.button(468, 582, 80, 30, "M7 sis", "M905 P1"); pg.ledsock(554, 590, 1509, "M7")
pg.button(578, 582, 70, 30, "M8 sıvı", "M905 P2"); pg.ledsock(654, 590, 1510, "M8")
d.text((358, 622), "Çap düzeltmesi: ölçülen Ø − nominal Ø (aşınmada −).", font=f(11), fill=SUB)
d.text((358, 638), "Bitirme payı: delikte kaba tur + tam derinlikte son tur.", font=f(11), fill=SUB)

# ---- Sağ: çıktı ----
pg.panel(686, 58, 328, 600, "Çıktı")
y = 96
for lab, n, u, fmt in [("Gereken boru boyu", 1526, "mm", "%4.1f"), ("En küçük X0", 1527, "mm", "%4.1f"), ("Kesim süresi", 1528, "dk", "%4.1f")]:
    pg.row(698, y, lab, n, u, ro=True, fmt=fmt, lw=146); y += 34
d.rectangle([698, 204, 1002, 410], fill=(42, 52, 62), outline=EDGE)
d.text((708, 208), "Takım yolu", font=f(13), fill=(170, 180, 190))
pg.ctrls.append(("TOOLPATH", "", 700, 226, 300, 182, "Toolpath kontrolü", "", ""))
pg.button(698, 420, 146, 34, "Kaydet", "M907", note="tubemill.dat")
pg.button(856, 420, 146, 34, "Yükle", "M908", note="tubemill.dat")
pg.button(698, 462, 146, 34, "Varsayılan", "M901")
pg.button(856, 462, 146, 34, "Simülasyon", "M909", note="tubemillsim.html")
pg.button(698, 506, 304, 54, "Kod üret", "M900", primary=True)
pg.note(698, 570, 304, ["Z0: boru üstü, takım ucuyla değdir (A0).", "Y0: takım boru merkezinin tam üstünde.", "İlk deneme takım havadayken (Z ofset)."], h=62)

pg.status()
pg.button(10, 706, 200, 48, "Delikler / uç >>", "OEM:2", note="2. sayfaya git")
pg.button(870, 706, 144, 48, "Çıkış", "EXIT", note="kaydet + wizard'dan çık")
pg.save("tubemill_bg.bmp", "tubemill_bg.png", "yerlesim_mill1.csv")

# önizleme (örnek değerlerle)
from PIL import ImageDraw
p = pg.img.copy(); pd = Px(ImageDraw.Draw(p))
ex = {1501: "40.000", 1502: "40.000", 1503: "40.000", 1504: "2.000", 1505: "2.000", 1506: "90.00", 1507: "90.00", 1508: "10.000", 1509: "300.000",
      1510: "1", 1511: "6.000", 1512: "15.000", 1513: "12000", 1514: "400", 1515: "100", 1516: "0.500", 1517: "0.500", 1518: "50", 1519: "10.000",
      1520: "3.0", 1522: "2.00", 1523: "0.000", 1525: "0.000", 1529: "0.000", 1526: "317.0", 1527: "1.0", 1528: "5.7"}
for c in pg.ctrls:
    if c[0] == "DRO" and c[1] in ex: pd.text((c[2] + 6, c[3] + 5), ex[c[1]], font=f(14), fill=TXT)
    if c[0] == "LED" and c[6].split()[-1] in ("1500", "1503", "1508", "1511"): pd.ellipse([c[2], c[3], c[2] + 14, c[3] + 14], fill=(40, 200, 60))
pd.text((18, 673), "Program hazir - 1 parca, kesim suresi ~5.7 dk. Ilk denemeyi havada yapin, sonra Cycle Start", font=f(13), fill=TXT)
p.save("tubemill_onizleme.png")
