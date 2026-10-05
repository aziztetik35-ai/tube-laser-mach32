import struct,sys
def rs(d,q):
    L=d[q]; q+=1
    if L==0xFF: L=struct.unpack_from("<H",d,q)[0]; q+=2
    return d[q:q+L].decode("cp1254","replace"), q+L
def parse(d):
    n=struct.unpack_from("<i",d,0)[0]; p=4; out=[]
    for i in range(n):
        st=p; f,k,pg=struct.unpack_from("<3i",d,p); q=p+12; ss=[]
        for _ in range(3): s,q=rs(d,q); ss.append(s)
        a,b=struct.unpack_from("<2i",d,q); q+=8
        txt,q=rs(d,q); std,oem=struct.unpack_from("<2i",d,q); q+=20
        fmt,q=rs(d,q); q+=4; r=struct.unpack_from("<4i",d,q); q+=16
        out.append(dict(i=i,st=st,en=q,f=f,k=k,pg=pg,ss=ss,ab=(a,b),txt=txt,std=std,oem=oem,fmt=fmt,r=r)); p=q
    return out,p
d=open(sys.argv[1],"rb").read(); o,p=parse(d)
print("kayıt",len(o),"bitiş",p,"dosya",len(d))
for x in o:
    if any(w in (x["txt"]+" ".join(x["ss"])) for w in ["Error","Ticker","Status","Message"]): print(x)
