from PIL import Image, ImageDraw, ImageFont
import math, csv

W,H = 1024,768
TW,TH = 1920,1080
SX,SY = TW/W, TH/H
from PIL import ImageDraw as _ID
class Px:
    def __init__(s,d): s.d=d
    def _b(s,b): return [b[0]*SX,b[1]*SY,b[2]*SX,b[3]*SY]
    def _p(s,ps):
        if ps and not isinstance(ps[0],(tuple,list)): ps=list(zip(ps[0::2],ps[1::2]))
        return [(p[0]*SX,p[1]*SY) for p in ps]
    def _k(s,k): k=dict(k); k["width"]=max(1,round(k.get("width",1)*SY)); return k
    def rectangle(s,b,**k): s.d.rectangle(s._b(b),**s._k(k))
    def rounded_rectangle(s,b,radius=0,**k): s.d.rounded_rectangle(s._b(b),radius=radius*SY,**s._k(k))
    def ellipse(s,b,**k): s.d.ellipse(s._b(b),**s._k(k))
    def arc(s,b,a1,a2,**k): s.d.arc(s._b(b),a1,a2,**s._k(k))
    def line(s,ps,**k): s.d.line(s._p(ps),**s._k(k))
    def polygon(s,ps,**k): s.d.polygon(s._p(ps),**k)
    def text(s,xy,t,**k): s.d.text((xy[0]*SX,xy[1]*SY),t,**k)
    def textlength(s,t,font): return s.d.textlength(t,font=font)/SX
import os
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vendor", "fonts") + os.sep
def f(sz,b=False): return ImageFont.truetype(F+("DejaVuSansCondensed-Bold.ttf" if b else "DejaVuSansCondensed.ttf"), round(sz*SY))

# ISA-101 tarzı gri HMI paleti
BG=(200,205,210); PANEL=(226,229,232); EDGE=(150,157,164); TXT=(31,42,51); SUB=(92,102,112)
FIELD=(255,255,255); RO=(208,213,218); BTN=(238,240,242); BTNE=(120,128,136)
PRI=(47,93,138); DRAW=(40,70,100); DIM=(150,80,20)

ctrls=[]  # (tip, ad, x,y,w,h, mach3, not)
def dro(n,x,y,w=100,h=28,ro=False,note=""): ctrls.append(("DRO",n,x,y,w,h,"OEM/User DRO %d"%n,("salt-okunur " if ro else "")+note))
def btn(t,x,y,w,h,g,note=""): ctrls.append(("BUTON",t,x,y,w,h,g,note))
def led(n,x,y,note=""): ctrls.append(("LED","",x,y,14,14,"User LED %d"%n,note))

img=Image.new("RGB",(TW,TH),BG); d=Px(ImageDraw.Draw(img))

def panel(x,y,w,h,title):
    d.rectangle([x,y,x+w,y+h],fill=PANEL,outline=EDGE)
    d.rectangle([x,y,x+w,y+30],fill=(212,216,220),outline=EDGE)
    d.text((x+12,y+6),title,font=f(16,True),fill=TXT)

def row(x,y,label,n,unit,ro=False,note="",lw=168):
    d.text((x,y+5),label,font=f(15),fill=TXT)
    bx=x+lw
    d.rectangle([bx,y,bx+100,y+28],fill=RO if ro else FIELD,outline=EDGE)
    d.text((bx+106,y+6),unit,font=f(13),fill=SUB)
    dro(n,bx,y,ro=ro,note=note)

def button(x,y,w,h,t,g,primary=False,note=""):
    d.rectangle([x+2,y+2,x+w+2,y+h+2],fill=(170,176,182))
    d.rectangle([x,y,x+w,y+h],fill=PRI if primary else BTN,outline=BTNE)
    fn=f(17 if primary else 15,True); tw=d.textlength(t,font=fn)
    d.text((x+(w-tw)/2,y+(h-18)/2),t,font=fn,fill=(255,255,255) if primary else TXT)
    btn(t,x,y,w,h,g,note)

def ledsock(x,y,n,note=""):
    d.rectangle([x-3,y-3,x+17,y+17],fill=(170,176,182),outline=EDGE); led(n,x,y,note)

def dimline(p1,p2,label,off=(0,0)):
    d.line([p1,p2],fill=DIM,width=1)
    for p,q in ((p1,p2),(p2,p1)):
        ang=math.atan2(q[1]-p[1],q[0]-p[0])
        for s in (0.45,-0.45):
            d.line([p,(p[0]+7*math.cos(ang+s),p[1]+7*math.sin(ang+s))],fill=DIM,width=1)
    mx=(p1[0]+p2[0])/2+off[0]; my=(p1[1]+p2[1])/2+off[1]
    d.text((mx,my),label,font=f(13,True),fill=DIM)

# Başlık
d.rectangle([0,0,W,48],fill=(58,72,86))
d.text((16,11),"Boru kesim sihirbazı",font=f(22,True),fill=(240,242,244))
d.text((W-300,17),"Mach3 · A ekseni · G93 ters zaman",font=f(13),fill=(190,198,206))

# 1) Profil
panel(10,58,326,600,"Profil")
button(22,100,120,36,"Yuvarlak","M802 P0")
ledsock(150,111,1000,"yuvarlak seçili")
button(176,100,120,36,"Dikdörtgen","M802 P1")
ledsock(304,111,1001,"dikdörtgen seçili")
# teknik çizimler
d.rectangle([22,148,324,300],fill=(244,246,247),outline=EDGE)
cx,cy,R,r=95,222,52,42
kk=SY/SX; Rx,rx=R*kk,r*kk
d.ellipse([cx-Rx,cy-R,cx+Rx,cy+R],outline=DRAW,width=2); d.ellipse([cx-rx,cy-r,cx+rx,cy+r],outline=DRAW,width=1)
d.line([cx-Rx-8,cy,cx+Rx+8,cy],fill=SUB); d.line([cx,cy-62,cx,cy+62],fill=SUB)
dimline((cx-Rx,cy+62),(cx+Rx,cy+62),"D",(-4,1))
d.text((cx+Rx-10,cy-R-2),"t",font=f(13,True),fill=DIM)
x0,y0,aw,bh=190,178,110,86
d.rounded_rectangle([x0,y0,x0+aw,y0+bh],radius=12,outline=DRAW,width=2)
d.rounded_rectangle([x0+8,y0+8,x0+aw-8,y0+bh-8],radius=6,outline=DRAW,width=1)
dimline((x0,y0+bh+12),(x0+aw,y0+bh+12),"A",(-4,1))
dimline((x0+aw+12,y0),(x0+aw+12,y0+bh),"B",(4,-8))
d.text((x0+aw-22,y0-2),"R",font=f(13,True),fill=DIM); d.text((x0+10,y0+10),"t",font=f(12,True),fill=DIM)
y=316
for lab,n,u in [("Çap  D",1001,"mm"),("Genişlik  A",1002,"mm"),("Yükseklik  B",1003,"mm"),("Et kalınlığı  t",1004,"mm"),("Köşe radyüsü  R",1005,"mm")]:
    row(22,y,lab,n,u); y+=38
# dikdörtgen kesim şekli
d.rectangle([22,508,324,586],fill=(236,238,240),outline=EDGE)
d.text((32,514),"Dikdörtgen kesim şekli",font=f(14,True),fill=TXT)
button(32,542,110,32,"Kenar kenar","M805 P0")
ledsock(148,551,1003,"kenar kenar seçili")
button(176,542,110,32,"Tek seferde","M805 P1")
ledsock(292,551,1004,"tek seferde seçili")
# sabit bilgi
d.rectangle([22,594,324,646],fill=(236,238,240),outline=EDGE)
d.text((32,600),"Z0 = boru üst yüzeyi,  X0 = boru ucu (değdirme)",font=f(13),fill=SUB)
d.text((32,620),"Tek seferde modunda R köşe radyüsü kullanılır",font=f(13),fill=SUB)

# 2) Kesim
panel(346,58,332,600,"Kesim")
d.rectangle([358,96,666,212],fill=(244,246,247),outline=EDGE)
# boru ucu solda (X0 = değdirme), ayna sağda boruyu sürer, kafa sabit
ty1,ty2=132,176
d.rectangle([630,112,656,196],fill=(180,186,192),outline=DRAW)   # ayna
d.text((632,99),"ayna",font=f(11),fill=SUB)
d.text((366,99),"boru ucu",font=f(11),fill=SUB)
d.polygon([(372,ty1),(444,ty1),(416,ty2),(372,ty2)],outline=DRAW,fill=(236,238,240))   # uç (fire)
d.polygon([(454,ty1),(554,ty1),(526,ty2),(426,ty2)],outline=DRAW,fill=(255,255,255))   # 1. parça
d.polygon([(564,ty1),(630,ty1),(630,ty2),(536,ty2)],outline=DRAW,fill=(255,255,255))   # devamı
d.line([(449,ty1),(421,ty2)],fill=(200,70,30),width=3)
d.line([(559,ty1),(531,ty2)],fill=(200,70,30),width=3)
xc1,xc2=(449+421)/2,(559+531)/2
# X0: boru ucundan ilk kesimin nötr noktasına
for yy in range(158,206,6): d.line([(xc1,yy),(xc1,min(yy+3,206))],fill=DIM)
d.line([(372,ty2+2),(372,206)],fill=DIM)
dimline((372,203),(xc1,203),"",(0,0))
d.text(((372+xc1)/2-10,188),"X0",font=f(13,True),fill=DIM)
d.arc([444-22*SY/SX,ty1-22,444+22*SY/SX,ty1+22],123,180,fill=DIM,width=2); d.text((404,ty1+8),"α1",font=f(13,True),fill=DIM)
d.arc([554-22*SY/SX,ty1-22,554+22*SY/SX,ty1+22],123,180,fill=DIM,width=2); d.text((514,ty1+8),"α2",font=f(13,True),fill=DIM)
# L: iki ardışık kesimin nötr noktaları arası
for xx in (xc1,xc2):
    for yy in range(150,112,-6): d.line([(xx,yy),(xx,max(yy-3,112))],fill=DIM)
dimline((xc1,116),(xc2,116),"",(0,0))
d.text(((xc1+xc2)/2-4,99),"L",font=f(13,True),fill=DIM)
d.text((466,182),"1. parça",font=f(11),fill=SUB)
d.text((572,182),"← besleme",font=f(11),fill=SUB)
for i,a in enumerate(["45°","60°","90°"]):
    button(358+i*104,224,96,34,a,"M801 P%s"%a[:-1],note="α1=α2=%s"%a)
y=272
for lab,n,u in [("Başlangıç açısı  α1",1006,"°"),("Bitiş açısı  α2",1007,"°"),("Boru ucundan  X0",1008,"mm"),("Parça boyu  L",1017,"mm"),("Parça adedi",1018,"ad"),("Kerf",1011,"mm"),("Lead-in",1015,"mm")]:
    row(358,y,lab,n,u); y+=38
d.rectangle([358,540,666,646],fill=(236,238,240),outline=EDGE)
d.text((368,548),"Hesaplanan",font=f(14,True),fill=TXT)
y=572
for lab,n,u in [("Gereken boru boyu",1020,"mm"),("En küçük X0",1021,"mm")]:
    row(368,y,lab,n,u,ro=True,note="M800 yazar"); y+=36
ledsock(640,550,1002,"çarpışma uyarısı (kırmızı) - M800 yazar")
d.text((548,550),"X0 kontrol",font=f(12),fill=SUB)

# 3) Proses
panel(688,58,326,600,"Proses")
y=100
for lab,n,u in [("Kesim hızı  F",1009,"mm/dk"),("Pierce süresi",1010,"s"),("Lazer gücü  S",1014,"S"),("Kesim yüksekliği",1013,"mm"),("Güvenli mesafe",1012,"mm"),("A segment açısı",1016,"°")]:
    row(700,y,lab,n,u,lw=150); y+=38
d.rectangle([700,330,1002,430],fill=(236,238,240),outline=EDGE)
d.text((710,336),"Giriş çentiği",font=f(14,True),fill=TXT)
row(710,356,"Uzunluk (0 = yok)",1022,"mm",lw=140)
button(710,394,116,28,"Ayna tarafı","M806 P0")
ledsock(832,401,1005,"çentik ayna tarafı")
button(858,394,116,28,"Uç tarafı","M806 P1")
ledsock(980,401,1006,"çentik uç tarafı")
d.rectangle([700,440,1002,646],fill=(42,52,62),outline=EDGE)
d.text((710,446),"Takım yolu önizleme",font=f(13),fill=(170,180,190))
ctrls.append(("TOOLPATH","",702,466,298,178,"Toolpath kontrolü",""))

# Alt çubuk
d.rectangle([10,668,1014,694],fill=(244,246,247),outline=EDGE)
ctrls.append(("LABEL","",14,671,996,20,"Status (durum satırı)","Message() buraya yazar"))
button(10,706,120,48,"Varsayılan","M799")
button(136,706,120,48,"Kaydet","M803")
button(262,706,120,48,"Yükle","M804")
button(388,706,120,48,"Delikler / uç","SCRIPT:SetPage(2)",note="2. sayfaya geçer")
button(514,706,120,48,"Simülasyon","M807",note="3B simülasyonu açar")
button(640,706,220,48,"Kod üret","M800",primary=True,note="teach file yazar + yükler")
button(870,706,144,48,"Çıkış","Mach3 wizard Exit",note="kaydet + wizard'dan çık")

img.save("tube_wizard_bg.bmp"); img.save("tube_wizard_bg.png")

# Önizleme: örnek değerler + LED'ler + takım yolu
p=img.copy(); pd=Px(ImageDraw.Draw(p))
vals={1001:"60.000",1002:"40.000",1003:"40.000",1004:"2.000",1005:"3.000",1006:"45.000",1007:"45.000",1008:"30.000",
      1017:"250.000",1018:"4",1011:"0.200",1015:"2.000",1009:"1800",1010:"0.400",1014:"800",1013:"1.000",1012:"15.000",1016:"2.000",1022:"3.000",1020:"1030.800",1021:"22.500"}
for c in ctrls:
    t,n,x,y,w,h,_,_=c
    if t=="DRO" and n in vals:
        s=vals[n]; tw=pd.textlength(s,font=f(16,True)); pd.text((x+w-6-tw,y+5),s,font=f(16,True),fill=TXT)
    if t=="LED":
        col=(40,190,70) if ("yuvarlak" in c[7] or "tek seferde" in c[7] or "uç tarafı" in c[7]) else ((90,96,102))
        pd.rectangle([x,y,x+14,y+14],fill=col)
pd.text((18,673),"Parametreler yüklendi.",font=f(13),fill=TXT)
cx0,cy0=720,600
for k in range(4):
    xs=730+k*66
    pts=[]
    for j in range(0,361,6):
        ph=math.radians(j); pts.append((xs+18*math.cos(ph)+20*math.sin(ph)*0.5, 632-j*0.44))
    pd.line(pts,fill=(90,220,110),width=2)
pd.line([(720,636),(990,636)],fill=(90,110,130)); pd.line([(720,470),(720,636)],fill=(90,110,130))
p.save("tube_wizard_onizleme.png")

with open("yerlesim.csv","w",newline="",encoding="utf-8-sig") as fh:
    w=csv.writer(fh,delimiter=";"); w.writerow(["Tip","Etiket","X","Y","W","H","Mach3 / G-kod","Not"])
    for c in ctrls: w.writerow(c)
print(len(ctrls))
