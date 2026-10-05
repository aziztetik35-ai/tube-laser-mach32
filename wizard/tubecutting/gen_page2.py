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


# ============ SAYFA 2: DELİKLER VE UÇ ŞEKLİ ============
d.rectangle([0,0,W,48],fill=(58,72,86))
d.text((16,11),"Boru kesim sihirbazı",font=f(22,True),fill=(240,242,244))
d.text((198,16),"·  Delikler ve uç şekli",font=f(16),fill=(200,208,216))
d.text((W-300,17),"Mach3 · A ekseni · G93 ters zaman",font=f(13),fill=(190,198,206))

# ---- Sol panel: uç şekli ----
panel(10,58,326,600,"Uç şekli")
button(22,100,120,36,"Gönye","M808 P0")
ledsock(150,111,1007,"gönye seçili")
button(176,100,120,36,"Balık ağzı","M808 P1")
ledsock(304,111,1008,"balık ağzı seçili")

# çizim: karşı boruya oturan balık ağzı (yandan)
d.rectangle([22,148,324,318],fill=(244,246,247),outline=EDGE)
cxp,cyp,Rp=258,233,52          # karşı boru (kesit, daire)
kk=SY/SX
d.ellipse([cxp-Rp*kk,cyp-Rp,cxp+Rp*kk,cyp+Rp],outline=DRAW,width=2,fill=(232,235,238))
d.ellipse([cxp-(Rp-7)*kk,cyp-(Rp-7),cxp+(Rp-7)*kk,cyp+(Rp-7)],outline=DRAW,width=1)
# parça borusu: soldan gelir, ucu karşı boruya oturur
rt=26
pts=[(40,cyp-rt)]
import math as _m
for i in range(0,41):
    yy=cyp-rt+2*rt*i/40
    xx=cxp-_m.sqrt(max(Rp*Rp-(yy-cyp)**2,0))*kk
    pts.append((xx,yy))
pts.append((40,cyp+rt))
d.polygon(pts,outline=DRAW,fill=(255,255,255))
d.line([(cxp-_m.sqrt(Rp*Rp-rt*rt)*kk-2,cyp-rt),(cxp-Rp*kk,cyp)],fill=(200,70,30),width=3)
d.line([(cxp-Rp*kk,cyp),(cxp-_m.sqrt(Rp*Rp-rt*rt)*kk-2,cyp+rt)],fill=(200,70,30),width=3)
d.text((52,cyp-8),"parça",font=f(12),fill=SUB)
d.text((cxp-18,cyp-8),"karşı",font=f(11),fill=SUB)
d.text((cxp-16,cyp+5),"boru",font=f(11),fill=SUB)
dimline((cxp-Rp*kk,cyp+Rp+12),(cxp+Rp*kk,cyp+Rp+12),"",(0,0))
d.text((cxp-14,cyp+Rp+14),"Ø K",font=f(12,True),fill=DIM)
d.text((34,156),"θ = birleşim açısı (90° = dik T birleşim)",font=f(11),fill=SUB)

d.text((22,330),"Balık ağzı hangi uca",font=f(14,True),fill=TXT)
button(22,352,76,32,"Uç yönü","M809 P0")
ledsock(104,361,1009,"uç yönü (sağ)")
button(124,352,76,32,"Ayna yönü","M809 P1")
ledsock(206,361,1010,"ayna yönü (sol)")
button(226,352,76,32,"İki uç","M809 P2")
ledsock(308,361,1011,"iki uç")
y=400
for lab,n,u in [("Karşı boru  Ø K",1032,"mm"),("Birleşim açısı  θ",1033,"°")]:
    row(22,y,lab,n,u); y+=38
d.rectangle([22,486,324,646],fill=(236,238,240),outline=EDGE)
for i,t in enumerate(["Balık ağzı seçilince her parçanın iki ucu","ayrı kesilir, parçalar arasında fire kalır.","Diğer uç, ana sayfadaki α1 / α2 açısıyla","gönye kesilir.","","Ø K, dikdörtgende profil yüksekliği B'den,","yuvarlakta boru çapından küçük olamaz."]):
    d.text((32,494+i*20),t,font=f(13),fill=SUB)

# ---- Sağ panel: delikler (seç → tip → konum → ölçü) ----
panel(346,58,668,600,"Delikler")
def step(n,x,y,t):
    d.ellipse([x,y,x+20*SY/SX,y+20],fill=PRI)
    d.text((x+6*SY/SX*1.0,y+2),str(n),font=f(13,True),fill=(255,255,255))
    d.text((x+28,y+1),t,font=f(15,True),fill=TXT)
# 1) delik seç
step(1,358,94,"Delik seç")
for i in range(8):
    x=358+i*41
    button(x,120,36,32,str(i+1),"M810 P%d"%(i+1))
    ledsock(x+11,158,1020+i,"delik %d seçili"%(i+1))
# 2) tip
step(2,358,186,"Delik tipi")
tips=[("Yok",0),("Yuvarlak",1),("Oval",2),("Pencere",3)]
for i,(t,v) in enumerate(tips):
    x=358+i*83
    button(x,212,76,34,t,"M811 P%d"%v)
    ledsock(x+31,252,1030+v,"tip %s"%t.lower())
# 3) konum
step(3,358,280,"Konum")
d.text((358,308),"Parça başından",font=f(14),fill=TXT)
d.rectangle([524,304,624,332],fill=FIELD,outline=EDGE); d.text((630,310),"mm",font=f(13),fill=SUB)
ctrls.append(("DRO",1041,524,304,100,28,"OEM/User DRO 1041","fmt=%4.2f"))
for i in range(4):
    x=358+i*83
    button(x,340,76,30,"Yüzey %d"%(i+1),"M812 P%d"%i)
    ledsock(x+31,375,1034+i,"yüzey %d"%(i+1))
d.text((358,402),"Açı (yuvarlak boru)",font=f(14),fill=TXT)
d.rectangle([524,398,624,426],fill=FIELD,outline=EDGE); d.text((630,404),"°",font=f(13),fill=SUB)
ctrls.append(("DRO",1042,524,398,100,28,"OEM/User DRO 1042","fmt=%4.1f"))
d.text((358,436),"Ortadan kaydırma",font=f(14),fill=TXT)
d.rectangle([524,432,624,460],fill=FIELD,outline=EDGE); d.text((630,438),"mm",font=f(13),fill=SUB)
ctrls.append(("DRO",1043,524,432,100,28,"OEM/User DRO 1043","fmt=%4.2f"))
# 4) ölçü (başlıklar tipe göre değişir: UserLabel 1-3)
step(4,358,472,"Ölçü")
for i in range(3):
    y=498+i*34
    d.rectangle([358,y+2,518,y+26],fill=(236,238,240))
    ctrls.append(("ULABEL",i+1,360,y+4,156,20,"UserLabel%d"%(i+1),"tipe göre başlık"))
    d.rectangle([524,y,624,y+28],fill=FIELD,outline=EDGE)
    ctrls.append(("DRO",1044+i,524,y,100,28,"OEM/User DRO %d"%(1044+i),"fmt=%4.2f"))
d.text((358,602),"Seçili deliğe yazılır; başka deliğe",font=f(12),fill=SUB)
d.text((358,618),"geçince otomatik saklanır.",font=f(12),fill=SUB)

# sağ sütun: liste + açıklama çizimi
d.rectangle([700,90,1004,372],fill=(236,238,240),outline=EDGE)
d.text((712,96),"Tanımlı delikler",font=f(14,True),fill=TXT)
for i in range(8):
    y=122+i*30
    d.rectangle([708,y,996,y+26],fill=FIELD,outline=(200,205,210))
    ctrls.append(("ULABEL",11+i,712,y+3,280,20,"UserLabel%d"%(11+i),"delik %d özeti"%(i+1)))
d.rectangle([700,382,1004,646],fill=(244,246,247),outline=EDGE)
d.text((712,388),"Yüzey ve ölçü yönleri",font=f(14,True),fill=TXT)
# kesit: dikdörtgen, yüzey numaraları
kk=SY/SX
qx,qy,qa,qb=790,500,48,40
d.rounded_rectangle([qx-qa*kk,qy-qb,qx+qa*kk,qy+qb],radius=6,outline=DRAW,width=2,fill=(255,255,255))
d.text((qx-6,qy-qb-20),"1",font=f(14,True),fill=DIM)
d.text((qx+qa*kk+6,qy-9),"2",font=f(14,True),fill=DIM)
d.text((qx-6,qy+qb+4),"3",font=f(14,True),fill=DIM)
d.text((qx-qa*kk-16,qy-9),"4",font=f(14,True),fill=DIM)
d.text((qx-34,qy-8),"kesit",font=f(11),fill=SUB)
d.text((712,572),"Yüzey n, A = (n-1)×90° iken üstte",font=f(11),fill=SUB)
d.text((712,588),"kalan yüzeydir (1: 0°, 2: 90°, …).",font=f(11),fill=SUB)
# yandan: parça, X ölçüsü, boy / en
px0,py0=872,448
d.rectangle([px0,py0,px0+118,py0+44],outline=DRAW,width=2,fill=(255,255,255))
d.rounded_rectangle([px0+60,py0+12,px0+96,py0+30],radius=7,outline=(200,70,30),width=2)
dimline((px0,py0+58),(px0+78,py0+58),"",(0,0)); d.text((px0+26,py0+60),"X",font=f(12,True),fill=DIM)
d.line([(px0+78,py0+30),(px0+78,py0+62)],fill=DIM)
dimline((px0+60,py0-8),(px0+96,py0-8),"",(0,0)); d.text((px0+64,py0-24),"Boy",font=f(11,True),fill=DIM)
d.text((px0+100,py0+14),"En",font=f(11,True),fill=DIM)
d.text((px0,py0+78),"X: parçanın boru",font=f(11),fill=SUB)
d.text((px0,py0+92),"ucu tarafından",font=f(11),fill=SUB)
d.text((712,612),"Boy: boru ekseni yönünde, En: çevre yönünde.",font=f(11),fill=SUB)
d.text((712,626),"Delme deliğin ortasında yapılır.",font=f(11),fill=SUB)

# ---- Alt çubuk ----
d.rectangle([10,668,1014,694],fill=(244,246,247),outline=EDGE)
ctrls.append(("LABEL","",14,671,996,20,"Status (durum satırı)","Message() buraya yazar"))
button(10,706,150,48,"Ana sayfa","SCRIPT:SetPage(1)",note="1. sayfaya döner")
button(170,706,150,48,"Kaydet","M803")
button(514,706,120,48,"Simülasyon","M807",note="3B simülasyonu açar")
button(640,706,220,48,"Kod üret","M800",primary=True,note="teach file yazar + yükler")
button(870,706,144,48,"Çıkış","Mach3 wizard Exit",note="kaydet + wizard'dan çık")

img.save("tube_wizard_sayfa2.bmp"); img.save("tube_wizard_sayfa2.png")
p=img.copy(); pd=Px(ImageDraw.Draw(p))
vals={1041:"40.00",1042:"0.0",1043:"0.00",1044:"10.00",1045:"0.00",1046:"0.00",1032:"60.000",1033:"90.000"}
ul={1:"Çap (mm)",2:"-",3:"-",11:"1  Yuvarlak Ø10  ·  X 40  ·  Yüzey 1",12:"2  Oval 24 × 8  ·  X 90  ·  Yüzey 2",13:"3  Pencere 40 × 16 R3  ·  X 140  ·  Yüzey 3"}
for i in range(14,19): ul[i]="%d  -"%(i-10)
for c in ctrls:
    t,n,x,y,w,h,_,_=c
    if t=="DRO" and n in vals:
        sv=vals[n]; tw=pd.textlength(sv,font=f(15,True)); pd.text((x+w-6-tw,y+5),sv,font=f(15,True),fill=TXT)
    if t=="ULABEL": pd.text((x+2,y+1),ul.get(n,""),font=f(13),fill=TXT)
    if t=="LED":
        on=("gönye" in c[7] or "uç yönü" in c[7] or c[7] in ("delik 1 seçili","tip yuvarlak","yüzey 1"))
        pd.rectangle([x,y,x+14,y+14],fill=(40,190,70) if on else (90,96,102))
pd.text((18,673),"Sayfa 2: delikler ve uç şekli",font=f(13),fill=TXT)
p.save("tube_wizard_onizleme2.png")
with open("yerlesim2.csv","w",newline="",encoding="utf-8-sig") as fh:
    w=csv.writer(fh,delimiter=";"); w.writerow(["Tip","Etiket","X","Y","W","H","Mach3 / G-kod","Not"])
    for c in ctrls: w.writerow(c)
print(len(ctrls))
