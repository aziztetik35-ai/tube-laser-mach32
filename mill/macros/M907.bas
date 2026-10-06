' M907 - TubeMill parametrelerini kaydet (Addons\TubeMill\tubemill.dat)
' Sira: 1. satir surum (1), DRO 1500-1533, DRO 1600-1677 (delikler)
' Degerler x1000 tamsayi: ondalik ayirac (virgul/nokta) sorunu olmaz
SaveWizard()
mf = GetMainFolder()
If Right(mf, 1) <> "\" Then
  mf = mf & "\"
End If
dosya = mf & "Addons\TubeMill\tubemill.dat"
Open dosya For Output As #1
Print #1, 1
For i = 1500 To 1533
  v = GetUserDRO(i)
  Print #1, CLng(v * 1000)
Next i
For i = 1600 To 1677
  v = GetUserDRO(i)
  Print #1, CLng(v * 1000)
Next i
Close #1
Message "Parametreler kaydedildi (tubemill.dat)"
