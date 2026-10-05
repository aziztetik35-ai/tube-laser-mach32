' M809 - Balik agzi ucu (M809 P0 = uc yonu, P1 = ayna yonu, P2 = iki uc)
p = Param1()
SetUserDRO(1031, p)
SetUserLED(1009, 0)
SetUserLED(1010, 0)
SetUserLED(1011, 0)
If p = 0 Then
  SetUserLED(1009, 1)
  Message "Balik agzi: uc yonundeki uc"
End If
If p = 1 Then
  SetUserLED(1010, 1)
  Message "Balik agzi: ayna yonundeki uc"
End If
If p = 2 Then
  SetUserLED(1011, 1)
  Message "Balik agzi: iki uc"
End If
