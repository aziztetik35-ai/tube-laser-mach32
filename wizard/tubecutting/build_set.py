import struct, csv
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference")
exec(open(os.path.join(HERE, "..", "common", "setlib.py")).read().split('d=open')[0])
src=open(os.path.join(REF,"TubeCutting_ornek.set"),"rb").read()
BG=src[8:101]; TRAILER=src[621:]; assert len(TRAILER)==44
def s(t):
    b=t.encode("cp1252"); assert len(b)<255; return bytes([len(b)])+b
def rec(typ,kind,cap,code,oem,fmt,rect,page=1,img="None"):
    return (struct.pack("<3i",typ,kind,page)+s(cap)+s(code)+s(img)+b"\0"*8+s("Text")
            +struct.pack("<2i",0,oem)+b"\0"*12+s(fmt)+struct.pack("<i",0)
            +struct.pack("<4i",rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
DRO=lambda oem,r,fmt,pg: rec(12,1,"Text","None\r\n",oem,fmt,r,pg)
BTN=lambda cap,g,r,pg: rec(33,4,cap,g+"\r\n",0,"",r,pg)
SCR=lambda cap,sc,r,pg: rec(34,4,cap,sc,0,"",r,pg)
LED=lambda oem,r,pg: rec(56,6,"Text","None\r\n",oem,"",r,pg)
def build(objs): return struct.pack("<2i",1+len(objs),0)+BG+b"".join(objs)+TRAILER
# doğrulama
assert build([DRO(1001,(190,316,100,28),"%4.3f",1),DRO(1001,(191,355,100,28),"%4.3f",1),DRO(1001,(192,392,100,28),"%4.3f",1),
      BTN("Yuvarlak","M802 P0",(22,100,120,36),1),LED(1001,(304,111,14,14),1),LED(1000,(150,111,14,14),1)])==src
# 2. sayfa arka planı: BG kaydını sayfa 2 ve farklı resimle klonla
def bg_page(page,fname):
    b=BG; q=8; strs=[]
    for _ in range(3):
        L=b[q]; strs.append(b[q+1:q+1+L]); q+=1+L
    assert strs[2]==b"tube_wizard_bg.bmp", strs
    return struct.pack("<i",0)+b[0:4]+struct.pack("<i",page)+bytes([len(strs[0])])+strs[0]+bytes([len(strs[1])])+strs[1]+s(fname)+b[q:]
CAP={"Varsayılan":"Varsayilan","Çıkış":"Kapat","Ayna tarafı":"Ayna yönü","Uç tarafı":"Uç yönü","Balık ağzı":"Balik agzi","İki uç":"Iki uç"}
FMT1={1009:"%4.0f",1018:"%4.0f",1014:"%4.0f"}
objs=[]
for page,fn in ((1,"yerlesim.csv"),(2,"yerlesim2.csv")):
    for r in csv.reader(open(fn,encoding="utf-8-sig"),delimiter=";"):
        t=r[0]
        if t not in ("DRO","LED","BUTON"): continue
        x,y,w,h=map(int,r[2:6]); rc=(x,y,w,h)
        if t=="DRO":
            n=int(r[6].split()[-1]); fmt=r[7][4:] if r[7].startswith("fmt=") else FMT1.get(n,"%4.3f")
            objs.append(DRO(n,rc,fmt,page))
        elif t=="LED": objs.append(LED(int(r[6].split()[-1]),rc,page))
        else:
            cap=CAP.get(r[1],r[1]); cap.encode("cp1252")
            if r[1]=="Çıkış": objs.append(SCR(cap,"SaveWizard()\r\nDoOEMButton(231)",rc,page))
            elif r[6].startswith("SCRIPT:SetPage("):   # sayfa geçişi: 1024.set'teki gibi OEM n = n. sayfaya git
                pn=int(r[6][len("SCRIPT:SetPage("):-1]); objs.append(rec(32,4,cap,"None",pn,"",rc,page))
            elif r[6].startswith("SCRIPT:"): objs.append(SCR(cap,r[6][7:],rc,page))
            else: objs.append(BTN(cap,r[6],rc,page))
objs.insert(0,bg_page(2,"tube_wizard_sayfa2.bmp"))
d24=open(os.path.join(REF,"1024.set"),"rb").read(); o24,_=parse(d24)
er0=next(x for x in o24 if x['txt']=="Error")
def label_text(text,page,rect):
    b0=d24[er0['st']:er0['en']]; q=12
    for _ in range(3): q+=1+b0[q]
    q+=8; L=b0[q]; tail=b0[q+1+L:]; t=text.encode("cp1252")
    nb=bytearray(b0[:q]+bytes([len(t)])+t+tail); struct.pack_into("<i",nb,8,page)
    struct.pack_into("<4i",nb,len(nb)-16,rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]); return bytes(nb)
for page,fn in ((1,"yerlesim.csv"),(2,"yerlesim2.csv")):
    for r in csv.reader(open(fn,encoding="utf-8-sig"),delimiter=";"):
        if r[0]=="ULABEL":
            x,y,w,h=map(int,r[2:6]); objs.append(label_text("UserLabel%d"%int(r[1]),page,(x,y,w,h)))
# 1024.set'ten Toolpath (sayfa 1) ve Error etiketi (iki sayfa)
d24=open(os.path.join(REF,"1024.set"),"rb").read(); o24,_=parse(d24)
def clone(i,page,rect):
    x=o24[i]; b=bytearray(d24[x['st']:x['en']])
    struct.pack_into("<i",b,8,page); struct.pack_into("<4i",b,len(b)-16,rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]); return bytes(b)
tp=next(x['i'] for x in o24 if x['k']==11); er=next(x['i'] for x in o24 if x['txt']=="Error")
objs+= [clone(tp,1,(702,466,298,178)), clone(er,1,(14,671,996,20)), clone(er,2,(14,671,996,20))]
# Pick Wizard açıklama / yazar
dsh=open(os.path.join(REF,"Shapes.set"),"rb").read(); osh,_=parse(dsh)
def clone_label(i,text,rect):
    x=osh[i]; b=dsh[x['st']:x['en']]; q=12
    for _ in range(3): q+=1+b[q]
    q+=8; L=b[q]; tail=b[q+1+L:]; t=text.encode("cp1252")
    nb=bytearray(b[:q]+bytes([len(t)])+t+tail); struct.pack_into("<i",nb,8,1)
    struct.pack_into("<4i",nb,len(nb)-16,rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]); return bytes(nb)
di=next(x['i'] for x in osh if x['txt'].startswith("Desc ")); ai=next(x['i'] for x in osh if x['txt'].startswith("Author "))
objs+= [clone_label(di,"Desc Boru lazer kesim - gonye, balik agzi, delik",(0,-40,200,17)), clone_label(ai,"Author Atetik",(0,-22,200,17))]
out=build(objs)
o2,p2=parse(out); assert p2==len(out)-44 and len(o2)==len(objs)+1
open("TubeCutting.set","wb").write(out)
from collections import Counter
print(len(o2),"kayıt;", "sayfa:",Counter(x['pg'] for x in o2), "arka planlar:",[(x['pg'],x['ss'][2]) for x in o2 if x['k']==3])
print("scriptler:",[(x['pg'],x['ss'][0],x['ss'][1]) for x in o2 if x['f']==34])
