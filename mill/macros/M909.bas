' M909 - Freze simulasyonunu ac (Addons\TubeMill\tubemillsim.html)
mf = GetMainFolder()
If Right(mf, 1) <> "\" Then
  mf = mf & "\"
End If
dosya = mf & "Addons\TubeMill\tubemillsim.html"
If Dir(dosya) = "" Then
  Message "HATA: tubemillsim.html bulunamadi"
Else
  If Dir(mf & "Addons\TubeMill\tubemill_data.js") = "" Then
    Message "Once Kod uret - simulasyon verisi yok"
  Else
    Message "Simulasyon aciliyor"
  End If
  res = Shell("explorer.exe " & Chr(34) & dosya & Chr(34), 1)
End If
