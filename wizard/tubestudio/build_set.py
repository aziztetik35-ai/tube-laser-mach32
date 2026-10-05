import struct, csv
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "..", "reference")
exec(open(os.path.join(HERE, "..", "common", "setlib.py")).read().split('d=open')[0])
src=open(os.path.join(REF,"TubeCutting_ornek.set"),"rb").read()
BG=src[8:101]; TRAILER=src[621:]
def s(t):
    b=t.encode("cp1252"); assert len(b)<255; return bytes([len(b)])+b
def rec(typ,kind,cap,code,oem,fmt,rect,page=1,img="None"):
    return (struct.pack("<3i",typ,kind,page)+s(cap)+s(code)+s(img)+b"\0"*8+s("Text")
            +struct.pack("<2i",0,oem)+b"\0"*12+s(fmt)+struct.pack("<i",0)
            +struct.pack("<4i",rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
def bg_page(page,fname):
    b=BG; q=8; strs=[]
    for _ in range(3):
        L=b[q]; strs.append(b[q+1:q+1+L]); q+=1+L
    return struct.pack("<i",0)+b[0:4]+struct.pack("<i",page)+bytes([len(strs[0])])+strs[0]+bytes([len(strs[1])])+strs[1]+s(fname)+b[q:]
d24=open(os.path.join(REF,"1024.set"),"rb").read(); o24,_=parse(d24)
def clone_rect(i,page,rect):
    x=o24[i]; b=bytearray(d24[x['st']:x['en']]); struct.pack_into("<i",b,8,page)
    struct.pack_into("<4i",b,len(b)-16,rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]); return bytes(b)
er0=next(x for x in o24 if x['txt']=="Error"); tp=next(x['i'] for x in o24 if x['k']==11)
def label_text(text,rect,page=1):
    b0=d24[er0['st']:er0['en']]; q=12
    for _ in range(3): q+=1+b0[q]
    q+=8; L=b0[q]; tail=b0[q+1+L:]; t=text.encode("cp1252")
    nb=bytearray(b0[:q]+bytes([len(t)])+t+tail); struct.pack_into("<i",nb,8,page)
    struct.pack_into("<4i",nb,len(nb)-16,rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]); return bytes(nb)
CAP={"İçe aktar":"Içe aktar","Çıkış":"Kapat"}
objs=[]
for r in csv.reader(open("yerlesim_studio.csv",encoding="utf-8-sig"),delimiter=";"):
    t=r[0]
    if t=="Tip": continue
    x,y,w,h=map(int,r[2:6]); rc=(x,y,w,h)
    if t=="BUTON":
        cap=CAP.get(r[1],r[1])
        if r[1]=="Çıkış": objs.append(rec(34,4,cap,"SaveWizard()\r\nDoOEMButton(231)",0,"",rc))
        else: objs.append(rec(33,4,cap,r[6]+"\r\n",0,"",rc))
    elif t=="ULABEL": objs.append(label_text("UserLabel%d"%int(r[1]),rc))
    elif t=="TOOLPATH": objs.append(clone_rect(tp,1,rc))
    elif t=="LABEL": objs.append(label_text("Error",rc))
dsh=open(os.path.join(REF,"Shapes.set"),"rb").read(); osh,_=parse(dsh)
objs.append(label_text("Desc Tube Studio - tarayici konfigurator + ice aktar",(0,-40,200,17)))
objs.append(label_text("Author Atetik",(0,-22,200,17)))
out=struct.pack("<i",1+len(objs))+bg_page(1,"tubestudio_bg.bmp")+b"".join(objs)+TRAILER
o2,p2=parse(out); assert p2==len(out)-44 and len(o2)==len(objs)+1
open("TubeStudio.set","wb").write(out)
print(len(o2),"kayıt;",[(x['ss'][0],x['ss'][1].strip()[:30]) for x in o2 if x['k']==4],[x['txt'] for x in o2 if x['k']==7])
