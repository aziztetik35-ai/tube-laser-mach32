# Claude Code ile çalışma

## İlk oturumda Claude Code'a yapıştır
```
Bu depo Mach3 tabanlı tüp lazer makinamın yazılımı. Önce CLAUDE.md ve docs/DRO_MAP.md'yi oku.
Sonra: npm install, python tools/build_all.py, python tests/test_macros.py, node tests/studio_ui.test.js çalıştır.
Testlerin sonucunu ve proje yapısını 5-6 maddede özetle. Hiçbir dosyayı değiştirme.
```

## Değişiklik isterken kalıp
```
[İstek]. CLAUDE.md'deki kurallara uy. M800 değişiyorsa vb2js üzerinden Studio'nun da güncellendiğini
doğrula, gerekiyorsa tests/test_macros.py'ye yeni test durumu ekle. Build + iki testi çalıştır,
sonra değişiklikleri kısa özetle ve commit et. Kesim sırası, X0/Z0 veya G1/G93 düzeni değişiyorsa açıkça uyar.
```

## Örnek istekler
- "Tek seferde modunda köşe geçiş bölgesi ekle: A dönüşü köşeye N mm kala başlasın, N Studio'da ve wizard'da ayarlanabilsin."
- "Studio çizim editörüne delik etrafında ölçü (mesafe) gösterimi ekle: seçili deliğin parça uçlarına ve en yakın yüzey kenarına uzaklığı."
- "Studio'da serbest kontur (polyline) delik çizimi: M800'e kontur dosyasından okuma ekle."

## Makineye kurulum (Windows)
```
python tools/build_all.py
python tools/install.py --mach3 "C:\Mach3" --profile Mach3Mill --dry-run
python tools/install.py --mach3 "C:\Mach3" --profile Mach3Mill
```
Profil adı: Mach3 kısayolundaki `/p` parametresi veya `C:\Mach3\macros\` altındaki klasör adı.
