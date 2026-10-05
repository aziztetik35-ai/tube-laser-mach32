' M821 - Tube Studio'yu ac: guncel degerleri wizard_state.js'e yaz, tarayicida ac
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
mf = GetMainFolder()
If Right(mf, 1) <> "\" Then
  mf = mf & "\"
End If
f = mf & "Addons\TubeStudio\wizard_state.js"
Open f For Output As #1
Print #1, "var WIZARD_STATE = {"
For i = 1000 To 1033
  Print #1, i & ": " & GetUserDRO(i) & ","
Next i
For i = 1100 To 1297
  Print #1, i & ": " & GetUserDRO(i) & ","
Next i
Print #1, "vx: " & GetParam("VelocitiesX") * 60 & ", vy: " & GetParam("VelocitiesY") * 60 & ", vz: " & GetParam("VelocitiesZ") * 60 & ", va: " & GetParam("VelocitiesA") * 60
Print #1, "};"
Close #1
' --- Tube Studio wizard ozet satirlari (UserLabel 31-36)
If GetUserDRO(1000) = 0 Then
  zs = "Yuvarlak Ø" & GetUserDRO(1001)
Else
  zs = "Dikdörtgen " & GetUserDRO(1002) & " × " & GetUserDRO(1003)
  If GetUserDRO(1005) > 0 Then
    zs = zs & " R" & GetUserDRO(1005)
  End If
End If
SetUserLabel(31, "Profil:   " & zs & "   ·   et " & GetUserDRO(1004) & " mm")
SetUserLabel(32, "Kesim:   X0 " & GetUserDRO(1008) & "   ·   L " & GetUserDRO(1017) & "   ·   " & GetUserDRO(1018) & " adet   ·   gönye " & GetUserDRO(1006) & "° / " & GetUserDRO(1007) & "°")
zs = "Gönye"
If GetUserDRO(1030) = 1 Then
  zs = "Balik agzi Ø" & GetUserDRO(1032) & " / " & GetUserDRO(1033) & "°"
  If GetUserDRO(1031) = 0 Then
    zs = zs & "  (uç yönü)"
  End If
  If GetUserDRO(1031) = 1 Then
    zs = zs & "  (ayna yönü)"
  End If
  If GetUserDRO(1031) = 2 Then
    zs = zs & "  (iki uç)"
  End If
End If
If GetUserDRO(1000) = 1 Then
  If GetUserDRO(1019) = 1 Then
    zs = zs & "   ·   tek seferde"
  Else
    zs = zs & "   ·   kenar kenar"
  End If
End If
SetUserLabel(33, "Uç:   " & zs)
zn = 0
For zi = 0 To 19
  If GetUserDRO(1100 + zi * 10) >= 1 Then
    zn = zn + 1
  End If
Next zi
SetUserLabel(34, "Delik:   " & zn & " adet (her parçada)")
SetUserLabel(35, "Proses:   F " & GetUserDRO(1009) & "   ·   S " & GetUserDRO(1014) & "   ·   pierce " & GetUserDRO(1010) & " s   ·   kesim Z " & GetUserDRO(1013))
zs = "yok"
If GetUserDRO(1022) > 0 Then
  zs = GetUserDRO(1022) & " mm"
  If GetUserDRO(1023) = 0 Then
    zs = zs & ", ayna yönü"
  Else
    zs = zs & ", uç yönü"
  End If
End If
SetUserLabel(36, "Çentik:   " & zs)
h = mf & "Addons\TubeStudio\tubestudio.html"
If Dir(h) = "" Then
  Message "HATA: tubestudio.html bulunamadi"
Else
  res = Shell("explorer.exe " & Chr(34) & h & Chr(34), 1)
  Message "Tube Studio aciliyor - konfigurasyondan sonra 'Wizard'a gönder', burada 'Içe aktar'"
End If
