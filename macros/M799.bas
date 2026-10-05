' M799 - Varsayilan degerler (TubeCutting wizard DRO haritasi)
SetUserDRO(1000, 0)
SetUserDRO(1001, 50)
SetUserDRO(1002, 40)
SetUserDRO(1003, 40)
SetUserDRO(1004, 2)
SetUserDRO(1005, 0)
SetUserDRO(1006, 45)
SetUserDRO(1007, 45)
SetUserDRO(1008, 100)
SetUserDRO(1009, 1200)
SetUserDRO(1010, 0.3)
SetUserDRO(1011, 0.2)
SetUserDRO(1012, 25)
SetUserDRO(1013, 1)
SetUserDRO(1014, 800)
SetUserDRO(1015, 2)
SetUserDRO(1016, 2)
SetUserDRO(1017, 200)
SetUserDRO(1018, 1)
SetUserDRO(1019, 0)
SetUserDRO(1020, 0)
SetUserDRO(1022, 0)
SetUserDRO(1023, 1)
SetUserDRO(1021, 0)
SetUserLED(1000, 1)
SetUserLED(1001, 0)
SetUserLED(1002, 0)
SetUserLED(1003, 1)
SetUserLED(1004, 0)
SetUserLED(1005, 0)
SetUserLED(1006, 1)
SetUserDRO(1030, 0)
SetUserDRO(1031, 0)
SetUserDRO(1032, 60)
SetUserDRO(1033, 90)
For i = 1100 To 1297
  SetUserDRO(i, 0)
Next i
SetUserLED(1007, 1)
SetUserLED(1008, 0)
SetUserLED(1009, 1)
SetUserLED(1010, 0)
SetUserLED(1011, 0)
SetUserDRO(1039, 1)
For zi = 1040 To 1046
  SetUserDRO(zi, 0)
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
Message "Varsayilan degerler yuklendi"
