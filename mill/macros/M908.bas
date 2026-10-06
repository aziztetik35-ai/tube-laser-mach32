' M908 - TubeMill parametrelerini yukle (M907 ile ayni sira)
' Cikti DRO'lari (1526-1528) yuklenmez: Kod uret yeniden hesaplar
mf = GetMainFolder()
If Right(mf, 1) <> "\" Then
  mf = mf & "\"
End If
dosya = mf & "Addons\TubeMill\tubemill.dat"
If Dir(dosya) = "" Then
  Message "Kayit dosyasi yok - once Kaydet"
Else
  Open dosya For Input As #1
  Input #1, v
  If v <> 1 Then
    Close #1
    Message "HATA: tubemill.dat surumu taninmiyor"
  Else
    For i = 1500 To 1533
      If EOF(1) Then
        Exit For
      End If
      Input #1, v
      If i < 1526 Then
        SetUserDRO(i, v / 1000)
      End If
      If i > 1528 Then
        SetUserDRO(i, v / 1000)
      End If
    Next i
    For i = 1600 To 1677
      If EOF(1) Then
        Exit For
      End If
      Input #1, v
      SetUserDRO(i, v / 1000)
    Next i
    Close #1
    SetUserDRO(1526, 0)
    SetUserDRO(1527, 0)
    SetUserDRO(1528, 0)
    '--- MILL-LED basla (M900-M906 ve M908 icinde AYNI kalmali)
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
    Message "Parametreler yuklendi - Kod uret'e basin"
  End If
End If
