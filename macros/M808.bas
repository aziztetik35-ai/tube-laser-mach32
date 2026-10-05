' M808 - Uc sekli (M808 P0 = gonye, M808 P1 = balik agzi)
p = Param1()
SetUserDRO(1030, p)
If p = 0 Then
  SetUserLED(1007, 1)
  SetUserLED(1008, 0)
  Message "Uc sekli: gonye"
Else
  SetUserLED(1007, 0)
  SetUserLED(1008, 1)
  Message "Uc sekli: balik agzi"
End If
