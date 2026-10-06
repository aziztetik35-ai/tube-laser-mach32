'==========================================================
' M800.m1s  -  TUP LAZER KESIM  (v10 - wizard)
' Mach3 / Cypress Enable VB
'----------------------------------------------------------
' v16: delik siniri 20 (DRO 1100 + no*10, no = 0..19 -> 1100..1297)
' v15: alfa2 (DRO 1007) = parcanin arka (ayna tarafi) ucunun gonye acisi.
'      alfa1 <> alfa2 ise uclar ayri kesilir, parcalar arasinda fire kalir.
' v14: delik konum kontrolu, G-kodda delik basligi kendi konturunun onunde
' v13: X0 = boru ON UCU (degdirme). Kesim on uca en yakin parcadan baslar,
'      ayna boruyu X ekseninde surer, kafa X'te sabittir.
'      Adet = parca sayisi (gonyede ilk kesim on ucu kirpar).
'      Uc yonu = boru on ucu tarafi (-X), ayna yonu = ayna tarafi (+X).
' v12: Z0 boru ust yuzeyi (degdirme). Hesap merkezden yapilir, cikista zofs dusulur
' v11: delik sayfasi sec/tip/konum/olcu akisi (duzenleme DRO 1039-1046)
'
' v10 degisiklikleri:
'   - Delikler: 8 satir (DRO 1100 + satir*10 + sutun)
'       sutun 0 tip (0 yok, 1 yuvarlak, 2 oval/slot, 3 pencere)
'       1 X (parca basindan)  2 A (derece)  3 Y (yanal kaydirma)
'       4 L / cap  5 W  6 R (pencere kose radyusu)
'   - Balik agzi uc sekli: DRO 1030 (0 gonye, 1 balik agzi)
'       1031 uc (0 sag, 1 sol, 2 iki uc)  1032 karsi boru capi
'       1033 birlesim acisi
'   - Tum konturlar once nokta listesine yaziliyor,
'     tek bir ortak blok G-kodu uretiyor (G1 + G93).
'
' v9: G1 duzeltmesi, simulasyon verisi (tubesim_data.js)
' v8: giris centigi (1022 boy, 1023 taraf)
' v7: dikdortgende 'tek seferde' kesim (1019)
' v6: TubeCutting wizard DRO haritasi
'
' SIFIR NOKTASI KONVANSIYONU:
'   Z0 = boru UST YUZEYI (A0 konumunda degdirme ile alinir)
'        yuvarlak: merkezden R yukarida, dortgen: merkezden B/2 yukarida
'   Y0 = doner eksenin dusey duzlemi (nozul boru merkezinin ustunde)
'   X0 = boru ON UCU (degdirme). X arttikca boru ucundan uzaklasilir (aynaya dogru)
'   A0 = dortgende bir yuz tam yatay
'==========================================================

testmode = 0

'--- ayna on yuzu ile nozul arasinda birakilacak en az mesafe (mm)
aynapay = 25

'--- yuvarlakta gonye turunun basladigi aci (derece). 90 = notr bolge
basaci = 90

PI = 3.14159265358979

'--- nokta listesi (bir islem adimi)
Dim ex(8000)
Dim ey(8000)
Dim ez(8000)
Dim ea(8000)
Dim es(8000)
Dim et(8000)
Dim ep(8000)
Dim ek(8000)

If testmode = 1 Then
  tip   = 0
  Dt    = 50
  en    = 40
  boy   = 40
  beta  = 45
  beta2 = 45
  x0    = 100
  plen  = 200
  adet  = 1
  guc   = 800
  hiz   = 1200
  tdel  = 0.3
  stof  = 1
  kerf  = 0.2
  astep = 2
  oto   = 0
  lead  = 2
  guvz  = 25
  rk    = 3
  sekil = 1
  cent  = 0
  ctaraf = 1
  btip  = 0
  buc   = 0
  bcap  = 60
  bteta = 90
Else
  tip   = GetUserDRO(1000)
  Dt    = GetUserDRO(1001)
  en    = GetUserDRO(1002)
  boy   = GetUserDRO(1003)
  beta  = GetUserDRO(1006)
  beta2 = GetUserDRO(1007)
  x0    = GetUserDRO(1008)
  plen  = GetUserDRO(1017)
  adet  = GetUserDRO(1018)
  guc   = GetUserDRO(1014)
  hiz   = GetUserDRO(1009)
  tdel  = GetUserDRO(1010)
  stof  = GetUserDRO(1013)
  kerf  = GetUserDRO(1011)
  astep = GetUserDRO(1016)
  oto   = 0
  lead  = GetUserDRO(1015)
  guvz  = GetUserDRO(1012)
  rk    = GetUserDRO(1005)
  sekil = GetUserDRO(1019)
  cent  = GetUserDRO(1022)
  ctaraf = GetUserDRO(1023)
  btip  = GetUserDRO(1030)
  buc   = GetUserDRO(1031)
  bcap  = GetUserDRO(1032)
  bteta = GetUserDRO(1033)
End If

adet = Int(adet + 0.5)

If cent < 0 Then
  cent = 0
End If
' centik yonu: 0 = ayna yonu (+X), 1 = uc yonu (-X, boru on ucu)
cyon = -1
If ctaraf = 0 Then
  cyon = 1
End If
If btip <> 1 Then
  btip = 0
End If

If testmode = 0 Then
  ' --- seçili deligi sakla (düzenleme alani 1040-1046 -> 1100 + (no-1)*10)
  zc = Int(GetUserDRO(1039) + 0.5)
  If zc < 1 Then
    zc = 1
  End If
  If zc > 8 Then
    zc = 8
  End If
  zh = 1100 + (zc - 1) * 10
  For zi = 0 To 6
    SetUserDRO(zh + zi, GetUserDRO(1040 + zi))
  Next zi
  ' --- ekrani tazele: LED'ler, ölçü basliklari, delik listesi
  zc = Int(GetUserDRO(1039) + 0.5)
  If zc < 1 Then
    zc = 1
  End If
  If zc > 8 Then
    zc = 8
  End If
  For zi = 1 To 8
    SetUserLED(1019 + zi, 0)
  Next zi
  SetUserLED(1019 + zc, 1)
  zt = Int(GetUserDRO(1040) + 0.5)
  For zi = 0 To 3
    SetUserLED(1030 + zi, 0)
  Next zi
  If zt >= 0 Then
    If zt <= 3 Then
      SetUserLED(1030 + zt, 1)
    End If
  End If
  zk = Int(GetUserDRO(1042) / 90 + 0.5)
  zk = zk - 4 * Int(zk / 4)
  For zi = 0 To 3
    SetUserLED(1034 + zi, 0)
  Next zi
  SetUserLED(1034 + zk, 1)
  zl1 = "-"
  zl2 = "-"
  zl3 = "-"
  If zt = 1 Then
    zl1 = "Çap (mm)"
  End If
  If zt = 2 Then
    zl1 = "Boy (mm)"
    zl2 = "En (mm)"
  End If
  If zt = 3 Then
    zl1 = "Boy (mm)"
    zl2 = "En (mm)"
    zl3 = "Köse radyüsü (mm)"
  End If
  SetUserLabel(1, zl1)
  SetUserLabel(2, zl2)
  SetUserLabel(3, zl3)
  For zi = 1 To 8
    zh = 1100 + (zi - 1) * 10
    zt = Int(GetUserDRO(zh) + 0.5)
    zs = zi & "  -"
    If zt >= 1 Then
      If zt <= 3 Then
        zL = Int(GetUserDRO(zh + 4) * 100 + 0.5) / 100
        zW = Int(GetUserDRO(zh + 5) * 100 + 0.5) / 100
        zR = Int(GetUserDRO(zh + 6) * 100 + 0.5) / 100
        zX = Int(GetUserDRO(zh + 1) * 100 + 0.5) / 100
        zA = Int(GetUserDRO(zh + 2) * 10 + 0.5) / 10
        zY = Int(GetUserDRO(zh + 3) * 100 + 0.5) / 100
        If zt = 1 Then
          zs = zi & "  Yuvarlak Ø" & zL
        End If
        If zt = 2 Then
          zs = zi & "  Oval " & zL & " × " & zW
        End If
        If zt = 3 Then
          zs = zi & "  Pencere " & zL & " × " & zW
          If zR > 0 Then
            zs = zs & " R" & zR
          End If
        End If
        zs = zs & "  ·  X " & zX
        If GetUserDRO(1000) = 0 Then
          zs = zs & "  ·  A " & zA & "°"
        Else
          zk = Int(zA / 90 + 0.5)
          zk = zk - 4 * Int(zk / 4)
          zs = zs & "  ·  Yüzey " & (zk + 1)
        End If
        If zY <> 0 Then
          zs = zs & "  ·  ofset " & zY
        End If
      End If
    End If
    SetUserLabel(10 + zi, zs)
  Next zi
  SaveWizard()
End If

'---------------- OPERATOR KONTROLLERI ----------------
hata = ""

If beta2 <= 0 Then
  beta2 = beta
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
If hiz <= 0 Then
  hata = "HATA: Kesim hizi girilmemis"
End If
If guc <= 0 Then
  hata = "HATA: Lazer gucu girilmemis"
End If
If adet < 1 Then
  hata = "HATA: Adet en az 1 olmali"
End If
If x0 <= 0 Then
  hata = "HATA: Kesim mesafesi X0 girilmemis"
End If

If tip = 0 Then
  If Dt <= 0 Then
    hata = "HATA: Dis cap girilmemis"
  End If
Else
  If en <= 0 Then
    hata = "HATA: EN olcusu girilmemis"
  End If
  If boy <= 0 Then
    hata = "HATA: BOY olcusu girilmemis"
  End If
End If

If plen <= 0 Then
  hata = "HATA: Parca boyu girilmemis"
End If

If astep <= 0 Then
  astep = 2
End If
' nokta dizisi (8000) tasmasin
If astep < 0.1 Then
  astep = 0.1
End If
If lead <= 0 Then
  lead = 2
End If
If stof <= 0 Then
  stof = 1
End If
If guvz <= 0 Then
  guvz = 25
End If

Rb = bcap / 2
If btip = 1 Then
  If plen <= 0 Then
    hata = "HATA: Balik agzinda parca boyu girilmeli"
  End If
  If bteta < 15 Then
    hata = "HATA: Birlesim acisi 15 dereceden kucuk olamaz"
  End If
  If bteta > 90 Then
    hata = "HATA: Birlesim acisi 90 dereceden buyuk olamaz"
  End If
  If tip = 0 Then
    If Rb < Dt / 2 Then
      hata = "HATA: Karsi boru capi borunun capindan kucuk olamaz"
    End If
  Else
    If Rb < boy / 2 Then
      hata = "HATA: Karsi boru capi profil yuksekliginden (B) kucuk olamaz"
    End If
  End If
End If

SetUserLED(1002, 0)
SetUserDRO(1020, 0)
SetUserDRO(1021, 0)

'---------------- YAYILMA / PARCA ARALIGI / AYNA KONTROLU ----------------
If hata = "" Then

  mm = 0
  If beta < 89.999 Then
    mm = 1 / Tan(beta * PI / 180)
  End If
  mm2 = 0
  If beta2 < 89.999 Then
    mm2 = 1 / Tan(beta2 * PI / 180)
  End If
  ' ayri = 1: her parcanin iki ucu ayri kesilir (balik agzi veya alfa1 <> alfa2)
  ayri = 0
  If btip = 1 Then
    ayri = 1
  End If
  If Abs(beta2 - beta) > 0.001 Then
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
    tiltmax = Dt / 2
    nmax = Dt / 2
  Else
    tiltmax = en / 2
    nmax = boy / 2
    If sekil <> 1 Then
      tiltmax = en / 2 + lead
      nmax = boy / 2 + lead
    End If
  End If

  extG = mm * tiltmax
  extG2 = mm2 * tiltmax
  extB = 0
  If btip = 1 Then
    q = Rb * Rb - nmax * nmax
    If q < 0 Then
      q = 0
    End If
    extB = mb * tiltmax + (Rb - Sqr(q)) / sb
  End If

  ' extL: parcanin on (boru ucu, -X) ucundaki kesimin -X yonune tasmasi
  ' extR: parcanin arka (ayna, +X) ucundaki kesimin +X yonune tasmasi
  If ayri = 0 Then
    extL = extG
    extR = extG
    fire = 0
    pitch = plen + kerf
  Else
    extL = extG
    extR = extG2
    If btip = 1 Then
      If buc <> 1 Then
        extL = extB
      End If
      If buc <> 0 Then
        extR = extB
      End If
    End If
    fire = extR + extL + kerf + cent + 2
    pitch = plen + fire
  End If

  ' ilk kesim boru on ucunun disina tasmamali
  yayilma = extL
  If cyon < 0 Then
    yayilma = yayilma + cent
  End If
  minx0 = Int((yayilma + kerf / 2 + 1) * 1000 + 0.5) / 1000
  SetUserDRO(1021, minx0)
  If ayri = 0 Then
    SetUserDRO(1020, Int((x0 + adet * pitch + extR) * 1000 + 0.5) / 1000)
  Else
    SetUserDRO(1020, Int((x0 + (adet - 1) * pitch + plen + extR) * 1000 + 0.5) / 1000)
  End If

  If x0 < minx0 Then
    SetUserLED(1002, 1)
    hata = "HATA: X0 en az " & minx0 & " mm olmali - ilk kesim boru ucunun disina tasiyor"
  End If

  ' delikler parcanin icinde ve uc kesimlerinden uzak olmali
  For hno = 0 To 19
    hd = 1100 + hno * 10
    htip = Int(GetUserDRO(hd) + 0.5)
    If htip > 3 Then
      hata = "HATA: Delik " & (hno + 1) & " tipi gecersiz (0 yok, 1 yuvarlak, 2 oval, 3 pencere)"
    End If
    If htip >= 1 Then
      If htip <= 3 Then
        hx = GetUserDRO(hd + 1)
        hl = GetUserDRO(hd + 4)
        ' dikdortgende delik yuzeyin duz kisminda kalmali (kose yayina tasarsa kesim havada kalir)
        If tip = 1 Then
          hy = GetUserDRO(hd + 3)
          hw = GetUserDRO(hd + 5)
          If htip = 1 Then
            hw = hl
          End If
          kf = Int(GetUserDRO(hd + 2) / 90 + 0.5)
          kf = kf - 4 * Int(kf / 4)
          wf = en / 2
          If kf = 1 Then
            wf = boy / 2
          End If
          If kf = 3 Then
            wf = boy / 2
          End If
          rr = rk
          If rr < 0 Then
            rr = 0
          End If
          If rr > wf Then
            rr = wf
          End If
          If Abs(hy) + hw / 2 > wf - rr + 0.001 Then
            hata = "HATA: Delik " & (hno + 1) & " yuzeyin duz kismindan tasiyor - Y ofset + en/2 en cok " & (wf - rr) & " olmali"
          End If
        End If
        hmin = Int((extL + hl / 2) * 100 + 0.5) / 100
        hmax = Int((plen - extR - hl / 2) * 100 + 0.5) / 100
        If hx < hmin Then
          hata = "HATA: Delik " & (hno + 1) & " parcanin disinda veya uc kesimine cok yakin - X " & hmin & " ile " & hmax & " arasinda olmali"
        End If
        If hx > hmax Then
          hata = "HATA: Delik " & (hno + 1) & " parcanin disinda veya uc kesimine cok yakin - X " & hmin & " ile " & hmax & " arasinda olmali"
        End If
      End If
    End If
  Next hno

End If

'---------------- URETIM ----------------
If hata <> "" Then

  Message hata

Else

  res = OpenTeachFile("tup_kesim.tap")

  If res = 0 Then
    Message "HATA: Program dosyasi olusturulamadi"
  Else

    Message "Program uretiliyor..."

    Code "(TUP LAZER KESIM)"
    Code "G21 G90 G40 G94"
    Code "G64 P0.02"
    Code "M5"

    R = Dt / 2
    ha = en / 2
    hb = boy / 2
    ' Z0 = boru ust yuzeyi: merkez tabanli hesaptan zofs dusulur
    If tip = 0 Then
      zofs = R
      zguv = Int((R + guvz - zofs) * 1000 + 0.5) / 1000
    Else
      zofs = hb
      zguv = Int((Sqr(en * en + boy * boy) / 2 + guvz - zofs) * 1000 + 0.5) / 1000
    End If

    nadim = Int(360 / astep)
    If nadim < 12 Then
      nadim = 12
    End If
    adim = 360 / nadim

    re = rk
    If re < 0.5 Then
      re = 0.5
    End If
    If re > ha Then
      re = ha
    End If
    If re > hb Then
      re = hb
    End If
    ad = astep / 2
    If ad > 1 Then
      ad = 1
    End If
    If ad < 0.25 Then
      ad = 0.25
    End If
    nc = Int(90 / ad + 0.5)
    If nc < 6 Then
      nc = 6
    End If
    ov = lead
    If ov > ha - re Then
      ov = ha - re
    End If

    acur = 0
    lz = 0
    npart = 0

    '=========== PARCALAR: uctan aynaya dogru ===========
    ' boru on ucundan aynaya dogru: her parca icin
    '   1) on uc kesimi (gonyede sadece ilk parcada: on ucu kirpar)
    '   2) delikler (parca henuz borudan ayrilmadan)
    '   3) arka uc kesimi -> parca dusur
    For p = 0 To adet - 1

      xL = x0 + p * pitch
      ' xL / xR = parcanin net on / arka kenari. Kesim cizgisi kerf/2 fire tarafinda (kerf telafisi):
      ' ayri = 0'da arka kesim (xR + kerf/2) = sonraki parcanin on kesimi (xL + pitch - kerf/2)
      xR = xL + plen
      npart = npart + 1

      For js = 1 To 3

        '--- bu adimda ne yapilacak (0 = yok, 1 = uc kesimi, 2 = delikler)
        op = 1
        xf = 1
        xref = xL - kerf / 2
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
          xref = xR + kerf / 2
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
        ' gonye egimi: arka uc ayri kesiliyorsa alfa2
        mmc = mm
        If js = 3 Then
          If ayri = 1 Then
            mmc = mm2
          End If
        End If

        np = 0

        If op = 1 Then
          '================= UC KESIMI (gonye / balik agzi) =================
          If xf = 1 Then
            Code "(parca " & (p + 1) & " - gonye x" & Int(xref * 1000 + 0.5) / 1000 & ")"
          Else
            Code "(parca " & (p + 1) & " - balik agzi x" & Int(xref * 1000 + 0.5) / 1000 & ")"
          End If

          If tip = 0 Then
            '----- YUVARLAK -----
            s0 = basaci
            If xf <> 1 Then
              s0 = 0
            End If
            abase = 360 * Int((acur - s0) / 360 + 0.5)
            For i = 0 To nadim
              phi = s0 + i * adim
              u = R * Sin(phi * PI / 180)
              v = R * Cos(phi * PI / 180)
              If xf = 1 Then
                x = xref + mmc * v
              Else
                q = Rb * Rb - u * u
                If q < 0 Then
                  q = 0
                End If
                x = xref + v * mb + sg * (Rb - Sqr(q)) / sb
              End If
              If i = 0 Then
                If cent > 0 Then
                  np = np + 1
                  ex(np) = x + cyon * cent
                  ey(np) = 0
                  ez(np) = R + stof
                  ea(np) = abase + phi
                  es(np) = u
                  et(np) = v
                  ep(np) = 1
                End If
              End If
              np = np + 1
              ex(np) = x
              ey(np) = 0
              ez(np) = R + stof
              ea(np) = abase + phi
              es(np) = u
              et(np) = v
              ep(np) = 0
              If i = 0 Then
                If cent <= 0 Then
                  ep(np) = 1
                End If
              End If
            Next i
            acur = ea(np)

          Else
            If sekil = 1 Then
              '----- DIKDORTGEN - TEK SEFERDE -----
              ' duz kenarda A sabit, kosede A doner (Y+Z kose yayini izler)
              abase = 360 * Int(acur / 360 + 0.5)
              For k = 0 To 4
                jmax = nc
                If k = 4 Then
                  jmax = 0
                End If
                For j = 0 To jmax
                  nf = 1
                  If j = 0 Then
                    th = k * 90
                    If k = 0 Then
                      ue = ha - re
                      ve = hb
                    End If
                    If k = 1 Then
                      ue = ha
                      ve = 0 - (hb - re)
                    End If
                    If k = 2 Then
                      ue = 0 - (ha - re)
                      ve = 0 - hb
                    End If
                    If k = 3 Then
                      ue = 0 - ha
                      ve = hb - re
                    End If
                    If k = 4 Then
                      ue = ov
                      ve = hb
                    End If
                    ' yuz baslangici (onceki kosenin bitisi)
                    us = 0
                    vs = hb
                    If k = 1 Then
                      us = ha
                      vs = hb - re
                    End If
                    If k = 2 Then
                      us = ha - re
                      vs = 0 - hb
                    End If
                    If k = 3 Then
                      us = 0 - ha
                      vs = 0 - (hb - re)
                    End If
                    If k = 4 Then
                      us = 0 - (ha - re)
                      vs = hb
                    End If
                    If xf <> 1 Then
                      nf = Int(Sqr((ue - us) * (ue - us) + (ve - vs) * (ve - vs))) + 1
                    End If
                    If k = 0 Then
                      nf = nf + 1
                    End If
                  Else
                    cu = ha - re
                    cv = hb - re
                    If k = 1 Then
                      cv = 0 - cv
                    End If
                    If k = 2 Then
                      cu = 0 - cu
                      cv = 0 - cv
                    End If
                    If k = 3 Then
                      cu = 0 - cu
                    End If
                    th = k * 90 + j * 90 / nc
                  End If
                  For jf = 1 To nf
                    If j = 0 Then
                      If k = 0 Then
                        ' ilk nokta: ust yuz ortasi (delme), sonra yuz sonu
                        If jf = 1 Then
                          u = 0
                          v = hb
                        Else
                          u = (ue - 0) * (jf - 1) / (nf - 1)
                          v = hb
                        End If
                      Else
                        u = us + (ue - us) * jf / nf
                        v = vs + (ve - vs) * jf / nf
                      End If
                    Else
                      u = cu + re * Sin(th * PI / 180)
                      v = cv + re * Cos(th * PI / 180)
                    End If
                    If xf = 1 Then
                      x = xref + mmc * u
                    Else
                      q = Rb * Rb - v * v
                      If q < 0 Then
                        q = 0
                      End If
                      x = xref + u * mb + sg * (Rb - Sqr(q)) / sb
                    End If
                    tr = th * PI / 180
                    If np = 0 Then
                      If cent > 0 Then
                        np = np + 1
                        ex(np) = x + cyon * cent
                        ey(np) = u * Cos(tr) - v * Sin(tr)
                        ez(np) = u * Sin(tr) + v * Cos(tr) + stof
                        ea(np) = abase + th
                        es(np) = u
                        et(np) = v
                        ep(np) = 1
                      End If
                    End If
                    np = np + 1
                    ex(np) = x
                    ey(np) = u * Cos(tr) - v * Sin(tr)
                    ez(np) = u * Sin(tr) + v * Cos(tr) + stof
                    ea(np) = abase + th
                    es(np) = u
                    et(np) = v
                    ep(np) = 0
                    If np = 1 Then
                      ep(np) = 1
                    End If
                  Next jf
                Next j
              Next k
              acur = ea(np)

            Else
              '----- DIKDORTGEN - KENAR KENAR -----
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
                y1 = 0 - w - lead
                y2 = w + lead
                nf = 1
                If xf <> 1 Then
                  nf = Int(y2 - y1) + 1
                End If
                For jf = 0 To nf
                  y = y1 + (y2 - y1) * jf / nf
                  u = y * Cos(tr) + h * Sin(tr)
                  v = h * Cos(tr) - y * Sin(tr)
                  If xf = 1 Then
                    x = xref + mmc * u
                  Else
                    q = Rb * Rb - v * v
                    If q < 0 Then
                      q = 0
                    End If
                    x = xref + u * mb + sg * (Rb - Sqr(q)) / sb
                  End If
                  np = np + 1
                  ex(np) = x
                  ey(np) = y
                  ez(np) = h + stof
                  ea(np) = abase + th
                  es(np) = y
                  et(np) = h
                  ep(np) = 0
                  If jf = 0 Then
                    ep(np) = 1
                  End If
                Next jf
                acur = ea(np)
              Next k
            End If
          End If

        End If
        If op = 2 Then
          '================= DELIKLER (parca p) =================
          For hno = 0 To 19
            hd = 1100 + hno * 10
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
              ' kerf telafisi: kontur kerf/2 ice (delik olcusu = tasarim olcusu)
              L2 = hl / 2 - kerf / 2
              W2 = hw / 2 - kerf / 2
              hr = hr - kerf / 2
              If L2 < 0.01 Then
                L2 = 0.01
              End If
              If W2 < 0.01 Then
                W2 = 0.01
              End If
              If hr < 0 Then
                hr = 0
              End If
              xc = xL + hx
              If tip = 0 Then
                s0 = hang
                hh = R
              Else
                kf = Int(hang / 90 + 0.5)
                kf = kf - 4 * Int(kf / 4)
                s0 = kf * 90
                hh = hb
                If kf = 1 Then
                  hh = ha
                End If
                If kf = 3 Then
                  hh = ha
                End If
              End If
              abase = 360 * Int((acur - s0) / 360 + 0.5)

              ' kontur: (L2,0)'dan basla, saat yonu tersine
              ' delme: yeterince buyukse delik ortasinda (fire tarafi)
              For sgi = 0 To 9
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
                  If hr < 0.000001 Then
                    npt = 1
                  End If
                End If
                For qq = 1 To npt
                  yaz = 1
                  If sgi = 0 Then
                    xi = 0
                    eta = 0
                    If L2 <= 1 Then
                      yaz = 0
                    End If
                    If W2 <= 1 Then
                      yaz = 0
                    End If
                  End If
                  If sgi = 1 Then
                    xi = L2
                    eta = 0
                  End If
                  If sgi = 3 Then
                    xi = 0 - (L2 - hr)
                    eta = W2
                  End If
                  If sgi = 5 Then
                    xi = 0 - L2
                    eta = 0 - (W2 - hr)
                  End If
                  If sgi = 7 Then
                    xi = L2 - hr
                    eta = 0 - W2
                  End If
                  If sgi = 9 Then
                    xi = L2
                    eta = 0
                  End If
                  If sgi = 2 Then
                    cxi = L2 - hr
                    ceta = W2 - hr
                    a0 = 0
                  End If
                  If sgi = 4 Then
                    cxi = 0 - (L2 - hr)
                    ceta = W2 - hr
                    a0 = 90
                  End If
                  If sgi = 6 Then
                    cxi = 0 - (L2 - hr)
                    ceta = 0 - (W2 - hr)
                    a0 = 180
                  End If
                  If sgi = 8 Then
                    cxi = L2 - hr
                    ceta = 0 - (W2 - hr)
                    a0 = 270
                  End If
                  If sgi = 2 Then
                    xi = cxi + hr * Cos((a0 + qq * 5) * PI / 180)
                    eta = ceta + hr * Sin((a0 + qq * 5) * PI / 180)
                  End If
                  If sgi = 4 Then
                    xi = cxi + hr * Cos((a0 + qq * 5) * PI / 180)
                    eta = ceta + hr * Sin((a0 + qq * 5) * PI / 180)
                  End If
                  If sgi = 6 Then
                    xi = cxi + hr * Cos((a0 + qq * 5) * PI / 180)
                    eta = ceta + hr * Sin((a0 + qq * 5) * PI / 180)
                  End If
                  If sgi = 8 Then
                    xi = cxi + hr * Cos((a0 + qq * 5) * PI / 180)
                    eta = ceta + hr * Sin((a0 + qq * 5) * PI / 180)
                  End If
                  ' ayni noktayi tekrar yazma (sifir boylu kenarlar)
                  If np > 0 Then
                    If ep(np) = 0 Then
                      If sgi > 1 Then
                        If Abs(xi - lxi) < 0.0005 Then
                          If Abs(eta - leta) < 0.0005 Then
                            yaz = 0
                          End If
                        End If
                      End If
                    End If
                  End If
                  If yaz = 1 Then
                    np = np + 1
                    ex(np) = xc + xi
                    If tip = 0 Then
                      aang = s0 + (hy + eta) / R * 180 / PI
                      ey(np) = 0
                      ez(np) = R + stof
                      ea(np) = abase + aang
                      es(np) = R * Sin(aang * PI / 180)
                      et(np) = R * Cos(aang * PI / 180)
                    Else
                      ey(np) = hy + eta
                      ez(np) = hh + stof
                      ea(np) = abase + s0
                      es(np) = hy + eta
                      et(np) = hh
                    End If
                    ep(np) = 0
                    ek(np) = 0
                    If sgi = 0 Then
                      ep(np) = 1
                      ek(np) = hno + 1
                    End If
                    If sgi = 1 Then
                      If L2 <= 1 Then
                        ep(np) = 1
                        ek(np) = hno + 1
                      End If
                      If W2 <= 1 Then
                        ep(np) = 1
                        ek(np) = hno + 1
                      End If
                    End If
                    lxi = xi
                    leta = eta
                  End If
                Next qq
              Next sgi
              acur = ea(np)
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
            If lz = 1 Then
              Code "G94"
              Code "M5"
              lz = 0
            End If
            Code "G0 Z" & zguv
            Code "G0 A" & aq
            Code "G0 X" & xs & " Y" & ys
            Code "G0 Z" & zs
            Code "M3 S" & guc
            Code "G4 P" & tdel
            Code "G93"
            lz = 1
          Else
            du = es(i) - es(i - 1)
            dv = et(i) - et(i - 1)
            dx = ex(i) - ex(i - 1)
            ds = Sqr(dx * dx + du * du + dv * dv)
            If ds > 0.000001 Then
              fs = Int(hiz / ds * 100 + 0.5) / 100
              Code "G1 X" & xs & " Y" & ys & " Z" & zs & " A" & aq & " F" & fs
            End If
          End If
        Next i
        If lz = 1 Then
          Code "G94"
          Code "M5"
          lz = 0
        End If
        If np > 0 Then
          Code "G0 Z" & zguv
        End If
        ' etiketleri temizle (sonraki adimda eski delik numarasi kalmasin)
        For i = 1 To np
          ek(i) = 0
        Next i

      Next js
    Next p

    Code "G0 Z" & zguv
    Code "G0 Y0"
    Code "M5"
    Code "M30"

    CloseTeachFile()
    LoadTeachFile()

    '--- simulasyon verisi (Addons\TubeCutting\tubesim_data.js)
    mf = GetMainFolder()
    If Right(mf, 1) <> "\" Then
      mf = mf & "\"
    End If
    gdosya = mf & "GCode\tup_kesim.tap"
    sdosya = mf & "Addons\TubeCutting\tubesim_data.js"
    If Dir(gdosya) <> "" Then
      q = Chr(34)
      Open gdosya For Input As #1
      Open sdosya For Output As #2
      Print #2, "var TUBE_DATA = {tip:" & tip & ", D:" & Dt & ", A:" & en & ", B:" & boy & ", R:" & rk & ", t:" & GetUserDRO(1004) & ", beta:" & beta & ", beta2:" & beta2 & ", x0:" & x0 & ", L:" & plen & ", adet:" & adet & ", kerf:" & kerf & ", stof:" & stof & ", sekil:" & sekil & ", cent:" & cent & ", ctaraf:" & ctaraf & ", hiz:" & hiz & ", zofs:" & zofs & ", btip:" & btip & ", buc:" & buc & ", bcap:" & bcap & ", bteta:" & bteta & ", vx:" & GetParam("VelocitiesX") * 60 & ", vy:" & GetParam("VelocitiesY") * 60 & ", vz:" & GetParam("VelocitiesZ") * 60 & ", va:" & GetParam("VelocitiesA") * 60 & "};"
      Print #2, "var TUBE_GCODE = ["
      For i = 1 To 500000
        If EOF(1) Then
          Exit For
        End If
        Line Input #1, satir
        Print #2, q & satir & q & ","
      Next i
      Print #2, q & q & "];"
      Close #2
      Close #1
    End If

    ' kenar kenar + egik uc: dik isin yan yuzde eti sabit X'te keser, egik duzlem et icinde
    ' cot(alfa) * t kadar kayar. Bu kerften buyukse koselerde kopru kalir (sanal isleme testi)
    uyari = ""
    If tip = 1 Then
      If sekil <> 1 Then
        egim = mm
        If mm2 > egim Then
          egim = mm2
        End If
        If btip = 1 Then
          egim = 1
        End If
        If egim * GetUserDRO(1004) > kerf Then
          uyari = "UYARI: kenar kenar egik kesimde koselerde kopru kalabilir - tek seferde onerilir. "
        End If
      End If
    End If
    Message uyari & "Program hazir - " & npart & " parca. Yolu kontrol edip Cycle Start"

  End If
End If
