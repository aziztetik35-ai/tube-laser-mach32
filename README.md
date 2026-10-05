# Tüp lazer kesim — Mach3 wizard'ları + Tube Studio

DIY tüp lazer (Mach3, döner A ekseni) için:
- **M800** makrosu: gönye (α1/α2), balık ağzı, 20'ye kadar delik (yuvarlak/oval/pencere), dikdörtgende tek seferde / kenar kenar kesim, giriş çentiği
- **TubeCutting** wizard'ı (klasik, 2 sayfa) ve **TubeStudio** wizard'ı (tarayıcı konfigüratörü + içe aktar)
- **tubestudio.html**: açınım üzerinde CAD tarzı delik çizimi, canlı 3B önizleme (M800'ün kendisiyle hesaplanır)
- **tubesim.html**: üretilen G-kodun 3B simülasyonu

## Elle kurulum (derleme gerekmez)
Depodaki `Mach3/` klasörü Mach3 klasör düzenindedir. İndir ve Mach3 kurulum klasörüne (ör. `C:\Mach3`) kopyala:

| Depoda | Mach3'te |
|---|---|
| `Mach3/macros/Mach3Mill/*.m1s` | `C:\Mach3\macros\<profil>\` (profil farklıysa o klasöre) |
| `Mach3/Addons/TubeCutting/` | `C:\Mach3\Addons\TubeCutting\` |
| `Mach3/Addons/TubeStudio/` | `C:\Mach3\Addons\TubeStudio\` |

Kopyalamadan önce eski dosyaların yedeğini al. Sonra Mach3'ü yeniden başlat.

## Hızlı başlangıç
```bash
python tools/build_all.py                                         # dist/Mach3/ altına derle
python tools/install.py --mach3 "C:\Mach3" --profile Mach3Mill    # Mach3'e kur (yedek alır)
```
Gereksinim: Python 3.10+ ve Pillow (`pip install pillow`). Testler için Node 18+ (`npm install`).

```bash
python tests/test_macros.py && node tests/studio_ui.test.js
```

## Makinede
- Sıfırlama: **X0 = boru ön ucu**, **Z0 = boru üst yüzeyi** (değdirme), A0 = yüz yatay.
- Wizards → Pick Wizard → **TubeCutting** veya **TubeStudio**.
- Studio: *Studio'yu aç* → konfigüre et → *Wizard'a gönder* (ilk seferde `Mach3\Addons\TubeStudio` klasörünü seç) → *İçe aktar* → *Kod üret*.
- Yeni bir değişiklikten sonraki ilk çalıştırmayı **lazer kapalıyken** yap.

Ayrıntı: `CLAUDE.md` (mimari ve kurallar), `docs/DRO_MAP.md`.
