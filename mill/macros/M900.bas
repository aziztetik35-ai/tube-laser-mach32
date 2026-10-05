'==========================================================
' M900.m1s  -  TUP FREZE: KESIM + DELIK  (TubeMill wizard)
' Mach3 / Cypress Enable VB
'----------------------------------------------------------
' Lazer kafasi yerine is mili (freze takimi) takilir.
' Kinematik lazerle ayni: kafa X'te sabit (Y, Z hareket eder),
' ayna boruyu X ekseninde surer ve A ekseninde dondurur.
'
' SIFIR NOKTASI:
'   X0 = boru ON UCU (takimla degdirme)
'   Z0 = boru UST YUZEYI, TAKIM UCUYLA (A0 konumunda). Takim degisince yeniden al.
'   Y0 = takim ekseni boru merkezinin tam ustunde (doner eksen duzlemi)
'   A0 = dikdortgende bir yuz tam yatay (Yuzey 1 ustte)
'
' TAKIM TELAFISI (G41/G42 YOK, yol makroda hesaplanir):
'   Uc kesimi: takim merkezi parca kenarindan rt kadar fire tarafinda.
'     Egik kenarda X kaydirmasi rt * Sqr(1 + egim^2) (egim = dx/ds).
'   Delik: kontur rt kadar ice kaydirilir. Delik capi = takim capi -> delme.
'
' KESIM:
'   Yuvarlak: takim radyal (Y0), A doner, derinlik her turda ap kadar
'     artar (helisel giris, dalma yok), sonra son tur tam derinlikte. G93.
'   Dikdortgen: yuz yuz. Takim boru disinda havada iner, yuzu Y boyunca
'     gecer (zikzak paso). Kose radyusu icin derinlik otomatik artar. G94.
'   Kesim izi = takim capi. Ayni cizgiyi paylasan kesim yalniz 90° gonyede.
'   Egik gonye veya balik agzinda her uc ayri kesilir, araya fire girer.
'
' DELIK (sabit A acisinda, XY konturu - matkap tezgahi gibi dik delik):
'   Konturda rampa ile iner (her turda ap), son tur tam derinlikte.
'   Delme (delik capi = takim capi): gagalama ile.
'   Yuvarlak boruda delik dik izdusumdur (lazer gibi cevreye sarilmaz).
'
' Delinme anindaki (et asildiktan sonra) ilerleme: F * son paso % / 100
'==========================================================

PI = 3.14159265358979
basaci = 90

Dim ex(40000)
Dim ey(40000)
Dim ez(40000)
Dim ea(40000)
Dim es(40000)
Dim ep(40000)
Dim ef(40000)
Dim eg(40000)
Dim ek(40000)
Dim cx(400)
Dim cy(400)
Dim cl(400)

tip    = Int(GetUserDRO(1500) + 0.5)
dcap   = GetUserDRO(1501)
en     = GetUserDRO(1502)
boy    = GetUserDRO(1503)
kal    = GetUserDRO(1504)
rk     = GetUserDRO(1505)
beta   = GetUserDRO(1506)
beta2  = GetUserDRO(1507)
x0     = GetUserDRO(1508)
plen   = GetUserDRO(1509)
adet   = Int(GetUserDRO(1510) + 0.5)
tcap   = GetUserDRO(1511)
tboy   = GetUserDRO(1512)
devir  = GetUserDRO(1513)
hiz    = GetUserDRO(1514)
hizz   = GetUserDRO(1515)
ap     = GetUserDRO(1516)
tasma  = GetUserDRO(1517)
sonpct = GetUserDRO(1518)
guvz   = GetUserDRO(1519)
bekle  = GetUserDRO(1520)
sogut  = Int(GetUserDRO(1521) + 0.5)
astep  = GetUserDRO(1522)
gaga   = GetUserDRO(1523)
yon    = Int(GetUserDRO(1524) + 0.5)
btip   = Int(GetUserDRO(1530) + 0.5)
buc    = Int(GetUserDRO(1531) + 0.5)
bcap   = GetUserDRO(1532)
bteta  = GetUserDRO(1533)

'--- MILL-LED basla (M900-M906 icinde AYNI kalmali)
zv = Int(GetUserDRO(1500) + 0.5)
SetUserLED(1500, 0)
SetUserLED(1501, 0)
If zv = 1 Then
  SetUserLED(1501, 1)
Else
  SetUserLED(1500, 1)
End If
zv = Int(GetUserDRO(1530) + 0.5)
SetUserLED(1503, 0)
SetUserLED(1504, 0)
If zv = 1 Then
  SetUserLED(1504, 1)
Else
  SetUserLED(1503, 1)
End If
zv = Int(GetUserDRO(1531) + 0.5)
For zi = 0 To 2
  SetUserLED(1505 + zi, 0)
Next zi
If zv >= 0 Then
  If zv <= 2 Then
    SetUserLED(1505 + zv, 1)
  End If
End If
zv = Int(GetUserDRO(1521) + 0.5)
For zi = 0 To 2
  SetUserLED(1508 + zi, 0)
Next zi
If zv >= 0 Then
  If zv <= 2 Then
    SetUserLED(1508 + zv, 1)
  End If
End If
zv = Int(GetUserDRO(1524) + 0.5)
SetUserLED(1511, 0)
SetUserLED(1512, 0)
If zv = 1 Then
  SetUserLED(1512, 1)
Else
  SetUserLED(1511, 1)
End If
'--- MILL-LED bitti
SaveWizard()

'---------------- OPERATOR KONTROLLERI ----------------
hata = ""

If beta2 <= 0 Then
  beta2 = beta
End If
If btip <> 1 Then
  btip = 0
End If
If tasma < 0 Then
  tasma = 0
End If
If sonpct <= 0 Then
  sonpct = 100
End If
If sonpct > 100 Then
  sonpct = 100
End If
If guvz <= 0 Then
  guvz = 10
End If
If bekle < 0 Then
  bekle = 0
End If
If astep <= 0 Then
  astep = 2
End If
If gaga < 0 Then
  gaga = 0
End If

If beta2 < 15 Then
  hata = "HATA: Bitis acisi alfa2 15 dereceden kucuk olamaz"
End If
If beta2 > 90 Then
  hata = "HATA: Bitis acisi alfa2 90 dereceden buyuk olamaz"
End If
If beta < 15 Then
  hata = "HATA: Aci 15 dereceden kucuk olamaz"
End If
If beta > 90 Then
  hata = "HATA: Aci 90 dereceden buyuk olamaz"
End If
If ap <= 0 Then
  hata = "HATA: Paso derinligi (ap) girilmemis"
End If
If hizz <= 0 Then
  hata = "HATA: Dalma ilerlemesi girilmemis"
End If
If hiz <= 0 Then
  hata = "HATA: Kesme ilerlemesi F girilmemis"
End If
If devir <= 0 Then
  hata = "HATA: Is mili devri girilmemis"
End If
If tboy <= 0 Then
  hata = "HATA: Takim kesme boyu girilmemis"
End If
If tcap <= 0 Then
  hata = "HATA: Takim capi girilmemis"
End If
If adet < 1 Then
  hata = "HATA: Adet en az 1 olmali"
End If
If plen <= 0 Then
  hata = "HATA: Parca boyu girilmemis"
End If
If x0 <= 0 Then
  hata = "HATA: X0 girilmemis"
End If
If kal <= 0 Then
  hata = "HATA: Et kalinligi girilmemis"
End If
If tip = 0 Then
  If dcap <= 0 Then
    hata = "HATA: Dis cap girilmemis"
  End If
  If kal * 2 >= dcap Then
    hata = "HATA: Et kalinligi capin yarisindan kucuk olmali"
  End If
Else
  If en <= 0 Then
    hata = "HATA: EN olcusu girilmemis"
  End If
  If boy <= 0 Then
    hata = "HATA: BOY olcusu girilmemis"
  End If
  If kal * 2 >= en Then
    hata = "HATA: Et kalinligi EN olcusunun yarisindan kucuk olmali"
  End If
  If kal * 2 >= boy Then
    hata = "HATA: Et kalinligi BOY olcusunun yarisindan kucuk olmali"
  End If
End If

Rb = bcap / 2
If btip = 1 Then
  If bteta < 15 Then
    hata = "HATA: Birlesim acisi 15 dereceden kucuk olamaz"
  End If
  If bteta > 90 Then
    hata = "HATA: Birlesim acisi 90 dereceden buyuk olamaz"
  End If
  If tip = 0 Then
    If Rb < dcap / 2 Then
      hata = "HATA: Karsi boru capi borunun capindan kucuk olamaz"
    End If
  Else
    If Rb < boy / 2 Then
      hata = "HATA: Karsi boru capi profil yuksekliginden (B) kucuk olamaz"
    End If
  End If
End If

SetUserLED(1502, 0)
SetUserDRO(1526, 0)
SetUserDRO(1527, 0)
SetUserDRO(1528, 0)

rt = tcap / 2
R = dcap / 2
ha = en / 2
hb = boy / 2

'---------------- DERINLIK / YAYILMA / PARCA ARALIGI ----------------
If hata = "" Then

  ' kose radyusu (dis). Ic kose radyusu = re - kal
  re = rk
  If re < 0 Then
    re = 0
  End If
  If re > ha Then
    re = ha
  End If
  If re > hb Then
    re = hb
  End If

  ' uc kesimi derinligi (yuzeyden)
  If tip = 0 Then
    dcut = kal + tasma
  Else
    ' dikdortgen: her yuz kendi duz yuzeyinden kesilir; kose yayindaki
    ' en derin et noktasi (45°) iki yuzden de bu kadar derinde kalir
    dk = kal
    If re > kal Then
      dc = re - (re - kal) * 0.70710678
      If dc > dk Then
        dk = dc
      End If
    End If
    dcut = dk + tasma
  End If
  dcut = Int(dcut * 1000 + 0.5) / 1000
  If dcut > tboy Then
    hata = "HATA: Kesim derinligi " & dcut & " mm takim kesme boyundan (" & tboy & " mm) buyuk"
  End If

  mm = 0
  If beta < 89.999 Then
    mm = 1 / Tan(beta * PI / 180)
  End If
  mm2 = 0
  If beta2 < 89.999 Then
    mm2 = 1 / Tan(beta2 * PI / 180)
  End If
  ' ayri = 1: her parcanin iki ucu ayri kesilir (90° disi gonye veya balik agzi)
  ayri = 0
  If btip = 1 Then
    ayri = 1
  End If
  If beta < 89.999 Then
    ayri = 1
  End If
  If beta2 < 89.999 Then
    ayri = 1
  End If
  mb = 0
  sb = 1
  If btip = 1 Then
    If bteta < 89.999 Then
      mb = 1 / Tan(bteta * PI / 180)
    End If
    sb = Sin(bteta * PI / 180)
  End If

  If tip = 0 Then
    tiltmax = R
    nmax = R
  Else
    tiltmax = ha
    nmax = hb
  End If

  ' kenar egimi (dx/ds) ust siniri -> takim kaydirma katsayisi k = Sqr(1 + egim^2)
  extG = mm * tiltmax
  extG2 = mm2 * tiltmax
  kG = Sqr(1 + mm * mm)
  kG2 = Sqr(1 + mm2 * mm2)
  extB = 0
  kB = 1
  If btip = 1 Then
    q = Rb * Rb - nmax * nmax
    If q < 0 Then
      q = 0
    End If
    extB = mb * tiltmax + (Rb - Sqr(q)) / sb
    fpb = 3
    If q > 0.000001 Then
      fpb = mb + nmax / Sqr(q) / sb
    End If
    If fpb > 3 Then
      fpb = 3
    End If
    kB = Sqr(1 + fpb * fpb)
  End If

  If ayri = 0 Then
    extL = 0
    extR = 0
    kL = 1
    kR = 1
    pitch = plen + tcap
  Else
    extL = extG
    kL = kG
    extR = extG2
    kR = kG2
    If btip = 1 Then
      If buc <> 1 Then
        extL = extB
        kL = kB
      End If
      If buc <> 0 Then
        extR = extB
        kR = kB
      End If
    End If
    fire = extL + extR + tcap * (kL + kR) + 2
    pitch = plen + fire
  End If

  minx0 = Int((extL + 1) * 1000 + 0.5) / 1000
  SetUserDRO(1527, minx0)
  SetUserDRO(1526, Int((x0 + (adet - 1) * pitch + plen + extR + tcap * kR + 1) * 1000 + 0.5) / 1000)
  If hata = "" Then
    If x0 < minx0 Then
      SetUserLED(1502, 1)
      hata = "HATA: X0 en az " & minx0 & " mm olmali - parca on ucu borunun disina tasiyor"
    End If
  End If

  ' delikler: parcanin icinde, takimdan buyuk, yuzeyde ve takim boyuna uygun
  For hno = 0 To 7
    hd = 1600 + hno * 10
    htip = Int(GetUserDRO(hd) + 0.5)
    If htip >= 1 Then
      If htip <= 3 Then
        hx = GetUserDRO(hd + 1)
        hang = GetUserDRO(hd + 2)
        hy = GetUserDRO(hd + 3)
        hl = GetUserDRO(hd + 4)
        hw = GetUserDRO(hd + 5)
        If htip = 1 Then
          hw = hl
        End If
        hmin = Int((extL + hl / 2) * 100 + 0.5) / 100
        hmax = Int((plen - extR - hl / 2) * 100 + 0.5) / 100
        If hx < hmin Then
          hata = "HATA: Delik " & (hno + 1) & " parcanin disinda veya uc kesimine cok yakin - X " & hmin & " ile " & hmax & " arasinda olmali"
        End If
        If hx > hmax Then
          hata = "HATA: Delik " & (hno + 1) & " parcanin disinda veya uc kesimine cok yakin - X " & hmin & " ile " & hmax & " arasinda olmali"
        End If
        If hl < tcap - 0.01 Then
          hata = "HATA: Delik " & (hno + 1) & " olcusu takim capindan (" & tcap & ") kucuk"
        End If
        If hw < tcap - 0.01 Then
          hata = "HATA: Delik " & (hno + 1) & " olcusu takim capindan (" & tcap & ") kucuk"
        End If
        W2 = hw / 2
        If tip = 0 Then
          ym = Abs(hy) + W2
          If ym > R - kal - 0.5 Then
            hata = "HATA: Delik " & (hno + 1) & " yuvarlak boruda cok genis veya cok yanda (Y ofset + en/2 < ic yaricap)"
          Else
            yn = Abs(hy) - W2
            If yn < 0 Then
              yn = 0
            End If
            dh = Sqr(R * R - yn * yn) - Sqr((R - kal) * (R - kal) - ym * ym) + tasma
            If dh > tboy Then
              hata = "HATA: Delik " & (hno + 1) & " derinligi " & Int(dh * 100 + 0.5) / 100 & " mm takim kesme boyundan buyuk"
            End If
          End If
        Else
          kf = Int(hang / 90 + 0.5)
          kf = kf - 4 * Int(kf / 4)
          wf = ha
          If kf = 1 Then
            wf = hb
          End If
          If kf = 3 Then
            wf = hb
          End If
          If Abs(hy) + W2 > wf - re + 0.001 Then
            hata = "HATA: Delik " & (hno + 1) & " yuzeyin duz kismindan tasiyor (Y ofset + en/2 <= " & (wf - re) & ")"
          End If
          If kal + tasma > tboy Then
            hata = "HATA: Delik " & (hno + 1) & " derinligi takim kesme boyundan buyuk"
          End If
        End If
      End If
    End If
  Next hno

End If

'---------------- URETIM ----------------
If hata <> "" Then

  Message hata

Else

  res = OpenTeachFile("tup_freze.tap")

  If res = 0 Then
    Message "HATA: Program dosyasi olusturulamadi"
  Else

    Message "Program uretiliyor..."

    If tip = 0 Then
      zofs = R
      zguv = Int((R + guvz - zofs) * 1000 + 0.5) / 1000
    Else
      zofs = hb
      zguv = Int((Sqr(en * en + boy * boy) / 2 + guvz - zofs) * 1000 + 0.5) / 1000
    End If

    Code "(TUP FREZE - TubeMill)"
    Code "(takim D" & tcap & " - Z0 boru ust yuzeyi takim ucuyla, Y0 boru merkezi)"
    Code "(kesim derinligi " & dcut & " - paso " & ap & ")"
    Code "G21 G90 G40 G49 G94 G17"
    Code "G64 P0.01"
    Code "G0 Z" & zguv
    Code "M3 S" & devir
    If bekle > 0 Then
      Code "G4 P" & bekle
    End If
    If sogut = 1 Then
      Code "M7"
    End If
    If sogut = 2 Then
      Code "M8"
    End If

    nadim = Int(360 / astep)
    If nadim < 36 Then
      nadim = 36
    End If
    adim = 360 / nadim
    hizs = hiz * sonpct / 100
    hizzs = hizz * sonpct / 100

    acur = 0
    gm = 94
    sure = 0
    npart = 0

    '=========== PARCALAR: uctan aynaya dogru ===========
    For p = 0 To adet - 1

      xL = x0 + p * pitch
      xR = xL + plen
      npart = npart + 1

      For js = 1 To 3

        op = 1
        xf = 1
        xref = xL
        yanx = -1
        If js = 1 Then
          If ayri = 0 Then
            If p > 0 Then
              op = 0
            End If
          Else
            If btip = 1 Then
              If buc <> 1 Then
                xf = 3
              End If
            End If
          End If
        End If
        If js = 2 Then
          op = 2
        End If
        If js = 3 Then
          xref = xR
          yanx = 1
          If btip = 1 Then
            If buc <> 0 Then
              xf = 2
            End If
          End If
        End If
        sg = 1
        If xf = 3 Then
          sg = -1
        End If
        mmc = mm
        If js = 3 Then
          If ayri = 1 Then
            mmc = mm2
          End If
        End If

        np = 0

        If op = 1 Then
          '================= UC KESIMI =================
          If js = 1 Then
            Code "(parca " & (p + 1) & " - on uc kesimi x" & Int(xref * 1000 + 0.5) / 1000 & ")"
          Else
            Code "(parca " & (p + 1) & " - arka uc kesimi x" & Int(xref * 1000 + 0.5) / 1000 & ")"
          End If

          If tip = 0 Then
            '----- YUVARLAK: helisel paso, takim radyal -----
            s0 = basaci
            If xf <> 1 Then
              s0 = 0
            End If
            abase = 360 * Int((acur - s0) / 360 + 0.5)
            zs0 = R + 0.5
            zb = R - dcut
            zthr = R - kal
            nl = Int((zs0 - zb) / ap)
            If nl * ap < zs0 - zb - 0.000001 Then
              nl = nl + 1
            End If
            If nl < 1 Then
              nl = 1
            End If
            nr = nl * nadim
            ntot = nr + nadim
            For i = 0 To ntot
              phi = s0 + i * adim
              sf = Sin(phi * PI / 180)
              cf = Cos(phi * PI / 180)
              u = R * sf
              v = R * cf
              If xf = 1 Then
                x = xref + mmc * v
                fp = 0 - mmc * sf
              Else
                q = Rb * Rb - u * u
                fp = 3
                If q > 0.000001 Then
                  fp = 0 - sf * mb + sg * u / Sqr(q) * cf / sb
                End If
                If q < 0 Then
                  q = 0
                End If
                x = xref + v * mb + sg * (Rb - Sqr(q)) / sb
              End If
              If fp > 3 Then
                fp = 3
              End If
              If fp < -3 Then
                fp = -3
              End If
              x = x + yanx * rt * Sqr(1 + fp * fp)
              z = zb
              If i <= nr Then
                z = zs0 - (zs0 - zb) * i / nr
              End If
              ff = hiz
              If z < zthr - 0.0001 Then
                ff = hizs
              End If
              If i = 0 Then
                np = np + 1
                ex(np) = x
                ey(np) = 0
                ez(np) = R + 1
                ea(np) = abase + phi
                es(np) = R * phi * PI / 180
                ep(np) = 1
                ef(np) = 0
                eg(np) = 1
                ff = hizz
              End If
              np = np + 1
              ex(np) = x
              ey(np) = 0
              ez(np) = z
              ea(np) = abase + phi
              es(np) = R * phi * PI / 180
              ep(np) = 0
              ef(np) = ff
              eg(np) = 1
            Next i
            acur = ea(np)

          Else
            '----- DIKDORTGEN: yuz yuz, takim boru disinda havada iner -----
            nl = Int(dcut / ap)
            If nl * ap < dcut - 0.000001 Then
              nl = nl + 1
            End If
            If nl < 1 Then
              nl = 1
            End If
            For k = 0 To 3
              th = k * 90
              tr = th * PI / 180
              If k = 1 Then
                h = ha
                w = hb
              Else
                If k = 3 Then
                  h = ha
                  w = hb
                Else
                  h = hb
                  w = ha
                End If
              End If
              abase = 360 * Int((acur - th) / 360 + 0.5)
              y1 = 0 - w - rt - 1
              y2 = w + rt + 1
              nf = 1
              If xf <> 1 Then
                nf = Int(y2 - y1) + 1
              End If
              For jl = 1 To nl
                dd = dcut * jl / nl
                zz = h - dd
                ff = hiz
                If dd > kal + 0.0001 Then
                  ff = hizs
                End If
                ya = y1
                yb = y2
                If jl - 2 * Int(jl / 2) = 0 Then
                  ya = y2
                  yb = y1
                End If
                For jf = 0 To nf
                  y = ya + (yb - ya) * jf / nf
                  u = y * Cos(tr) + h * Sin(tr)
                  v = h * Cos(tr) - y * Sin(tr)
                  If xf = 1 Then
                    x = xref + mmc * u
                    fp = mmc * Cos(tr)
                  Else
                    q = Rb * Rb - v * v
                    fp = 3
                    If q > 0.000001 Then
                      fp = mb * Cos(tr) - sg * v / Sqr(q) * Sin(tr) / sb
                    End If
                    If q < 0 Then
                      q = 0
                    End If
                    x = xref + u * mb + sg * (Rb - Sqr(q)) / sb
                  End If
                  If fp > 3 Then
                    fp = 3
                  End If
                  If fp < -3 Then
                    fp = -3
                  End If
                  x = x + yanx * rt * Sqr(1 + fp * fp)
                  If jf = 0 Then
                    If jl = 1 Then
                      np = np + 1
                      ex(np) = x
                      ey(np) = y
                      ez(np) = h + 1
                      ea(np) = abase + th
                      es(np) = 0
                      ep(np) = 1
                      ef(np) = 0
                      eg(np) = 0
                    End If
                    ' boru disinda havada iner
                    np = np + 1
                    ex(np) = x
                    ey(np) = y
                    ez(np) = zz
                    ea(np) = abase + th
                    es(np) = 0
                    ep(np) = 0
                    ef(np) = hizz
                    eg(np) = 0
                  Else
                    np = np + 1
                    ex(np) = x
                    ey(np) = y
                    ez(np) = zz
                    ea(np) = abase + th
                    es(np) = 0
                    ep(np) = 0
                    ef(np) = ff
                    eg(np) = 0
                  End If
                Next jf
              Next jl
              acur = abase + th
            Next k
          End If
        End If

        If op = 2 Then
          '================= DELIKLER (parca p) =================
          For hno = 0 To 7
            hd = 1600 + hno * 10
            htip = Int(GetUserDRO(hd) + 0.5)
            hx = GetUserDRO(hd + 1)
            hang = GetUserDRO(hd + 2)
            hy = GetUserDRO(hd + 3)
            hl = GetUserDRO(hd + 4)
            hw = GetUserDRO(hd + 5)
            hr = GetUserDRO(hd + 6)
            If htip = 1 Then
              hw = hl
              hr = hl / 2
            End If
            If htip = 2 Then
              hr = hl / 2
              If hw < hl Then
                hr = hw / 2
              End If
            End If
            If htip = 3 Then
              If hr < 0 Then
                hr = 0
              End If
              If hr > hl / 2 Then
                hr = hl / 2
              End If
              If hr > hw / 2 Then
                hr = hw / 2
              End If
            End If
            gecerli = 0
            If htip >= 1 Then
              If htip <= 3 Then
                If hl > 0 Then
                  If hw > 0 Then
                    gecerli = 1
                  End If
                End If
              End If
            End If

            If gecerli = 1 Then
              L2 = hl / 2
              W2 = hw / 2
              xc = xL + hx
              If tip = 0 Then
                s0 = hang
                ym = Abs(hy) + W2
                yn = Abs(hy) - W2
                If yn < 0 Then
                  yn = 0
                End If
                ztop = Sqr(R * R - yn * yn)
                zthr = Sqr((R - kal) * (R - kal) - ym * ym)
                zb = zthr - tasma
              Else
                kf = Int(hang / 90 + 0.5)
                kf = kf - 4 * Int(kf / 4)
                s0 = kf * 90
                h = hb
                If kf = 1 Then
                  h = ha
                End If
                If kf = 3 Then
                  h = ha
                End If
                ztop = h
                zthr = h - kal
                zb = zthr - tasma
              End If
              abase = 360 * Int((acur - s0) / 360 + 0.5)
              aa = abase + s0

              ' takim merkezi yolu: kontur rt kadar ice
              Lp = L2 - rt
              Wp = W2 - rt
              rp = hr - rt
              If Lp < 0 Then
                Lp = 0
              End If
              If Wp < 0 Then
                Wp = 0
              End If
              If rp < 0 Then
                rp = 0
              End If
              If rp > Lp Then
                rp = Lp
              End If
              If rp > Wp Then
                rp = Wp
              End If
              dmod = 0
              If Lp < 0.03 Then
                If Wp < 0.03 Then
                  dmod = 1
                End If
              End If
              ncn = 0
              cx(0) = 0
              cy(0) = 0
              If dmod = 0 Then
                If Wp < 0.03 Then
                  ' yiv (en = takim capi): eksen boyunca git-gel
                  cx(0) = 0 - Lp
                  cy(0) = 0
                  cx(1) = Lp
                  cy(1) = 0
                  cx(2) = 0 - Lp
                  cy(2) = 0
                  ncn = 2
                Else
                  If Lp < 0.03 Then
                    cx(0) = 0
                    cy(0) = 0 - Wp
                    cx(1) = 0
                    cy(1) = Wp
                    cx(2) = 0
                    cy(2) = 0 - Wp
                    ncn = 2
                  Else
                    ' koseleri rp yuvarlatilmis dikdortgen, (Lp,0)'dan saat yonu tersine
                    cx(0) = Lp
                    cy(0) = 0
                    ncn = 0
                    For sgi = 2 To 9
                      npt = 1
                      If sgi = 2 Then
                        npt = 18
                      End If
                      If sgi = 4 Then
                        npt = 18
                      End If
                      If sgi = 6 Then
                        npt = 18
                      End If
                      If sgi = 8 Then
                        npt = 18
                      End If
                      If npt = 18 Then
                        If rp < 0.000001 Then
                          npt = 1
                        End If
                      End If
                      qs = 1
                      If npt = 18 Then
                        qs = 0
                      End If
                      For qq = qs To npt
                        If sgi = 2 Then
                          ccx = Lp - rp
                          ccy = Wp - rp
                          a0 = 0
                        End If
                        If sgi = 4 Then
                          ccx = 0 - (Lp - rp)
                          ccy = Wp - rp
                          a0 = 90
                        End If
                        If sgi = 6 Then
                          ccx = 0 - (Lp - rp)
                          ccy = 0 - (Wp - rp)
                          a0 = 180
                        End If
                        If sgi = 8 Then
                          ccx = Lp - rp
                          ccy = 0 - (Wp - rp)
                          a0 = 270
                        End If
                        If sgi = 3 Then
                          xi = 0 - (Lp - rp)
                          eta = Wp
                        End If
                        If sgi = 5 Then
                          xi = 0 - Lp
                          eta = 0 - (Wp - rp)
                        End If
                        If sgi = 7 Then
                          xi = Lp - rp
                          eta = 0 - Wp
                        End If
                        If sgi = 9 Then
                          xi = Lp
                          eta = 0
                        End If
                        If npt = 18 Then
                          xi = ccx + rp * Cos((a0 + qq * 5) * PI / 180)
                          eta = ccy + rp * Sin((a0 + qq * 5) * PI / 180)
                        Else
                          If sgi = 2 Then
                            xi = Lp
                            eta = Wp
                          End If
                          If sgi = 4 Then
                            xi = 0 - Lp
                            eta = Wp
                          End If
                          If sgi = 6 Then
                            xi = 0 - Lp
                            eta = 0 - Wp
                          End If
                          If sgi = 8 Then
                            xi = Lp
                            eta = 0 - Wp
                          End If
                        End If
                        yaz = 1
                        If Abs(xi - cx(ncn)) < 0.0005 Then
                          If Abs(eta - cy(ncn)) < 0.0005 Then
                            yaz = 0
                          End If
                        End If
                        If yaz = 1 Then
                          ncn = ncn + 1
                          cx(ncn) = xi
                          cy(ncn) = eta
                        End If
                      Next qq
                    Next sgi
                    ' konvansiyonel: saat yonu (ters sira)
                    If yon = 1 Then
                      For j = 1 To Int(ncn / 2)
                        tx = cx(j)
                        ty = cy(j)
                        cx(j) = cx(ncn - j)
                        cy(j) = cy(ncn - j)
                        cx(ncn - j) = tx
                        cy(ncn - j) = ty
                      Next j
                    End If
                  End If
                End If
              End If

              ' yaklasma
              np = np + 1
              ex(np) = xc + cx(0)
              ey(np) = hy + cy(0)
              ez(np) = ztop + 1
              ea(np) = aa
              es(np) = 0
              ep(np) = 1
              ef(np) = 0
              eg(np) = 0
              ek(np) = hno + 1
              zs0 = ztop + 0.5
              np = np + 1
              ex(np) = xc + cx(0)
              ey(np) = hy + cy(0)
              ez(np) = zs0
              ea(np) = aa
              es(np) = 0
              ep(np) = 0
              ef(np) = hizz
              eg(np) = 0

              If dmod = 1 Then
                ' delme (gagalama)
                ngg = 1
                If gaga > 0 Then
                  ngg = Int((zs0 - zb) / gaga)
                  If ngg * gaga < zs0 - zb - 0.000001 Then
                    ngg = ngg + 1
                  End If
                End If
                If ngg < 1 Then
                  ngg = 1
                End If
                For j = 1 To ngg
                  z = zs0 - (zs0 - zb) * j / ngg
                  If j > 1 Then
                    np = np + 1
                    ex(np) = xc + cx(0)
                    ey(np) = hy + cy(0)
                    ez(np) = ztop + 1
                    ea(np) = aa
                    ep(np) = 2
                    eg(np) = 0
                    np = np + 1
                    ex(np) = xc + cx(0)
                    ey(np) = hy + cy(0)
                    ez(np) = zs0 - (zs0 - zb) * (j - 1) / ngg + 0.3
                    ea(np) = aa
                    ep(np) = 2
                    eg(np) = 0
                  End If
                  np = np + 1
                  ex(np) = xc + cx(0)
                  ey(np) = hy + cy(0)
                  ez(np) = z
                  ea(np) = aa
                  es(np) = 0
                  ep(np) = 0
                  ef(np) = hizz
                  If z < zthr - 0.0001 Then
                    ef(np) = hizzs
                  End If
                  eg(np) = 0
                Next j
              Else
                ' kontur boyunca rampa: her turda ap, son tur tam derinlikte
                cl(0) = 0
                For j = 1 To ncn
                  cl(j) = cl(j - 1) + Sqr((cx(j) - cx(j - 1)) * (cx(j) - cx(j - 1)) + (cy(j) - cy(j - 1)) * (cy(j) - cy(j - 1)))
                Next j
                nl = Int((zs0 - zb) / ap)
                If nl * ap < zs0 - zb - 0.000001 Then
                  nl = nl + 1
                End If
                If nl < 1 Then
                  nl = 1
                End If
                For lap = 0 To nl
                  For j = 1 To ncn
                    z = zb
                    If lap < nl Then
                      z = zs0 - (zs0 - zb) * (lap + cl(j) / cl(ncn)) / nl
                    End If
                    np = np + 1
                    ex(np) = xc + cx(j)
                    ey(np) = hy + cy(j)
                    ez(np) = z
                    ea(np) = aa
                    es(np) = 0
                    ep(np) = 0
                    ef(np) = hiz
                    If z < zthr - 0.0001 Then
                      ef(np) = hizs
                    End If
                    eg(np) = 0
                  Next j
                Next lap
              End If
              acur = aa
            End If
          Next hno
        End If

        '================= G-KOD CIKISI (ortak) =================
        For i = 1 To np
          xs = Int(ex(i) * 1000 + 0.5) / 1000
          ys = Int(ey(i) * 1000 + 0.5) / 1000
          zs = Int((ez(i) - zofs) * 1000 + 0.5) / 1000
          aq = Int(ea(i) * 1000 + 0.5) / 1000
          If ep(i) = 1 Then
            If ek(i) > 0 Then
              Code "(parca " & (p + 1) & " - delik " & ek(i) & ")"
            End If
            If gm = 93 Then
              Code "G94"
              gm = 94
            End If
            Code "G0 Z" & zguv
            Code "G0 A" & aq
            Code "G0 X" & xs & " Y" & ys
            Code "G0 Z" & zs
          End If
          If ep(i) = 2 Then
            Code "G0 Z" & zs
          End If
          If ep(i) = 0 Then
            dx = ex(i) - ex(i - 1)
            dy = ey(i) - ey(i - 1)
            dz = ez(i) - ez(i - 1)
            If eg(i) = 1 Then
              da = es(i) - es(i - 1)
              ds = Sqr(dx * dx + da * da + dz * dz)
              If ds > 0.000001 Then
                If gm <> 93 Then
                  Code "G93"
                  gm = 93
                End If
                fs = Int(ef(i) / ds * 100 + 0.5) / 100
                Code "G1 X" & xs & " Y" & ys & " Z" & zs & " A" & aq & " F" & fs
                sure = sure + ds / ef(i)
              End If
            Else
              ds = Sqr(dx * dx + dy * dy + dz * dz)
              If ds > 0.000001 Then
                If gm <> 94 Then
                  Code "G94"
                  gm = 94
                End If
                Code "G1 X" & xs & " Y" & ys & " Z" & zs & " F" & Int(ef(i) + 0.5)
                sure = sure + ds / ef(i)
              End If
            End If
          End If
        Next i
        If gm = 93 Then
          Code "G94"
          gm = 94
        End If
        If np > 0 Then
          Code "G0 Z" & zguv
        End If
        For i = 1 To np
          ek(i) = 0
        Next i

      Next js
    Next p

    Code "G0 Z" & zguv
    If sogut > 0 Then
      Code "M9"
    End If
    Code "M5"
    Code "G0 Y0"
    Code "M30"

    CloseTeachFile()
    LoadTeachFile()

    sdk = Int(sure * 10 + 0.5) / 10
    SetUserDRO(1528, sdk)
    Message "Program hazir - " & npart & " parca, kesim suresi ~" & sdk & " dk. Ilk denemeyi havada yapin, sonra Cycle Start"

  End If
End If
