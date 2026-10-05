' M807 - Simulasyonu ac (Addons\TubeCutting\tubesim.html)
mf = GetMainFolder()
If Right(mf, 1) <> "\" Then
  mf = mf & "\"
End If
f = mf & "Addons\TubeCutting\tubesim.html"
If Dir(f) = "" Then
  Message "HATA: tubesim.html bulunamadi"
Else
  If Dir(mf & "Addons\TubeCutting\tubesim_data.js") = "" Then
    Message "Once Kod uret - simulasyon verisi yok"
  End If
  res = Shell("explorer.exe " & Chr(34) & f & Chr(34), 1)
  Message "Simulasyon aciliyor"
End If
