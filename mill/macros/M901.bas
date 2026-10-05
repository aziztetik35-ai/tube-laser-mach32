' M901 - TubeMill varsayilan degerler (6 mm 2 agizli karbur freze, aluminyum)
SetUserDRO(1500, 0)
SetUserDRO(1501, 40)
SetUserDRO(1502, 40)
SetUserDRO(1503, 40)
SetUserDRO(1504, 2)
SetUserDRO(1505, 2)
SetUserDRO(1506, 90)
SetUserDRO(1507, 90)
SetUserDRO(1508, 10)
SetUserDRO(1509, 300)
SetUserDRO(1510, 1)
SetUserDRO(1511, 6)
SetUserDRO(1512, 15)
SetUserDRO(1513, 12000)
SetUserDRO(1514, 400)
SetUserDRO(1515, 100)
SetUserDRO(1516, 0.5)
SetUserDRO(1517, 0.5)
SetUserDRO(1518, 50)
SetUserDRO(1519, 10)
SetUserDRO(1520, 3)
SetUserDRO(1521, 0)
SetUserDRO(1522, 2)
SetUserDRO(1523, 0)
SetUserDRO(1524, 0)
SetUserDRO(1530, 0)
SetUserDRO(1531, 0)
SetUserDRO(1532, 50)
SetUserDRO(1533, 90)
' delikler (1600 + no*10 + sutun) temizle
For zh = 0 To 7
  For zc = 0 To 6
    SetUserDRO(1600 + zh * 10 + zc, 0)
  Next zc
Next zh
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
Message "Varsayilan degerler yuklendi - malzeme ve takima gore F, devir ve paso degerlerini kontrol edin"
