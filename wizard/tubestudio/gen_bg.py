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


# ============ TUBE STUDIO WIZARD ============
d.rectangle([0,0,W,48],fill=(58,72,86))
d.text((16,11),"Tube Studio",font=f(22,True),fill=(240,242,244))
d.text((150,16),"·  tarayıcıda konfigürasyon, Mach3'te kesim",font=f(16),fill=(200,208,216))
d.text((W-300,17),"Mach3 · A ekseni · G93 ters zaman",font=f(13),fill=(190,198,206))

panel(10,58,396,600,"Akış")
def stepbox(n,y,title,desc,bt,cmd,primary=False):
    d.ellipse([22,y+14,22+26*SY/SX,y+40],fill=PRI); d.text((22+8*SY/SX,y+17),str(n),font=f(15,True),fill=(255,255,255))
    button(60,y,334,54,bt,cmd,primary=primary)
    for i,t in enumerate(desc): d.text((60,y+62+i*17),t,font=f(12),fill=SUB)
stepbox(1,96,"","Konfigürasyonu tarayıcıda yapın ve canlı önizleyin;|bitince sağ üstteki 'Wizard'a gönder'e basın.".split("|"),"Studio'yu aç","M821")
stepbox(2,232,"","Studio'dan gönderilen konfigürasyonu alır;|değerler sağdaki özet listesinde görünür.".split("|"),"İçe aktar","M820")
stepbox(3,368,"","G-kodu M800 ile üretir ve Mach3'e yükler.|Önizleme ile aynı makro kullanılır.".split("|"),"Kod üret","M800",primary=True)
button(60,492,160,40,"Simülasyon","M807")
d.rectangle([22,548,394,646],fill=(236,238,240),outline=EDGE)
for i,t in enumerate(["İlk kullanım: Studio'da 'Wizard'a gönder'e ilk","basışta Mach3\\Addons\\TubeStudio klasörünü seçin.","Klasik sihirbaz (TubeCutting) aynı değerleri","kullanır; ikisi birlikte çalışabilir."]):
    d.text((32,556+i*20),t,font=f(12),fill=SUB)

panel(416,58,598,600,"Yüklü konfigürasyon")
for i in range(6):
    y=98+i*34
    d.rectangle([428,y,1002,y+28],fill=FIELD,outline=(200,205,210))
    ctrls.append(("ULABEL",31+i,434,y+4,562,20,"UserLabel%d"%(31+i),"özet"))
d.rectangle([428,312,1002,646],fill=(42,52,62),outline=EDGE)
d.text((438,318),"Takım yolu",font=f(13),fill=(170,180,190))
ctrls.append(("TOOLPATH","",430,338,570,306,"Toolpath kontrolü",""))

d.rectangle([10,668,1014,694],fill=(244,246,247),outline=EDGE)
ctrls.append(("LABEL","",14,671,996,20,"Status (durum satırı)","Message() buraya yazar"))
button(870,706,144,48,"Çıkış","Mach3 wizard Exit",note="kaydet + wizard'dan çık")

img.save("tubestudio_bg.bmp"); img.save("tubestudio_bg.png")
p=img.copy(); pd=Px(ImageDraw.Draw(p))
ex=["Profil:   Dikdörtgen 60 × 30 R3   ·   et 2 mm","Kesim:   X0 60   ·   L 300   ·   2 adet   ·   gönye 45° / 90°","Uç:   Gönye   ·   tek seferde","Delik:   2 adet (her parçada)","Proses:   F 1200   ·   S 800   ·   pierce 0.3 s   ·   kesim Z 1","Çentik:   yok"]
for c in ctrls:
    if c[0]=="ULABEL": pd.text((c[2]+2,c[3]+1),ex[c[1]-31],font=f(14),fill=TXT)
pd.text((18,673),"Konfigürasyon içe aktarıldı (24 değer) - Kod üret'e basın",font=f(13),fill=TXT)
p.save("tubestudio_onizleme.png")
with open("yerlesim_studio.csv","w",newline="",encoding="utf-8-sig") as fh:
    w=csv.writer(fh,delimiter=";"); w.writerow(["Tip","Etiket","X","Y","W","H","Mach3 / G-kod","Not"])
    for c in ctrls: w.writerow(c)
print(len(ctrls))
