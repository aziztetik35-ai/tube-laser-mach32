' M802 - Profil secimi (buton: M802 P0 = yuvarlak, M802 P1 = dikdortgen)
p = Param1()
SetUserDRO(1000, p)
If p = 0 Then
  SetUserLED(1000, 1)
  SetUserLED(1001, 0)
  Message "Profil: yuvarlak"
Else
  SetUserLED(1000, 0)
  SetUserLED(1001, 1)
  Message "Profil: dikdortgen"
End If
