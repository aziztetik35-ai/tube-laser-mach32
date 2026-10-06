' M906 - Delik kesim yonu (M906 P0 = tirmanma, P1 = konvansiyonel)
p = Int(Param1() + 0.5)
If p < 0 Then
  p = 0
End If
If p > 1 Then
  p = 1
End If
SetUserDRO(1524, p)
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
If p = 0 Then
  Message "Delik yonu: tirmanma (saat yonu tersi)"
End If
If p = 1 Then
  Message "Delik yonu: konvansiyonel (saat yonu)"
End If
