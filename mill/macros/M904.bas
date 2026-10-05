' M904 - Balik agzi ucu (M904 P0 = uc yonu, P1 = ayna yonu, P2 = iki uc)
p = Int(Param1() + 0.5)
If p < 0 Then
  p = 0
End If
If p > 2 Then
  p = 2
End If
SetUserDRO(1531, p)
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
If p = 0 Then
  Message "Balik agzi: uc yonu (on uc)"
End If
If p = 1 Then
  Message "Balik agzi: ayna yonu (arka uc)"
End If
If p = 2 Then
  Message "Balik agzi: iki uc"
End If
