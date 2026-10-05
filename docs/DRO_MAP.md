# DRO / LED / Etiket haritası

## User DRO (M800 girdileri)
| DRO | Anlam | Not |
|---|---|---|
| 1000 | Profil tipi | 0 yuvarlak, 1 dikdörtgen |
| 1001 | Çap D | yuvarlak |
| 1002 / 1003 | Genişlik A / Yükseklik B | dikdörtgen |
| 1004 | Et kalınlığı t | yalnız görsel/simülasyon |
| 1005 | Köşe radyüsü R | tek seferde yolu ve görsel |
| 1006 / 1007 | Başlangıç açısı α1 / Bitiş açısı α2 | α2 = 0 → α1; α1 ≠ α2 → uçlar ayrı kesilir |
| 1008 | X0 (boru ucundan ilk kesim) | |
| 1009 | Kesim hızı F | mm/dk |
| 1010 | Pierce süresi | s (G4 P, "ms" seçeneği kapalı olmalı) |
| 1011 | Kerf | |
| 1012 | Güvenli mesafe | yüzeyden |
| 1013 | Kesim yüksekliği (standoff) | |
| 1014 | Lazer gücü S | |
| 1015 | Lead-in | kenar kenar hava girişi, tek seferde bindirme |
| 1016 | A segment açısı | yuvarlak adım = bu değer, köşe adımı = yarısı (0.25–1°) |
| 1017 | Parça boyu L | |
| 1018 | Parça adedi | |
| 1019 | Dikdörtgen kesim şekli | 0 kenar kenar, 1 tek seferde |
| 1020 | (çıktı) Gereken boru boyu | M800 yazar |
| 1021 | (çıktı) En küçük X0 | M800 yazar |
| 1022 / 1023 | Giriş çentiği boyu / yönü | yön: 0 ayna (+X), 1 uç (−X) |
| 1030 | Uç şekli | 0 gönye, 1 balık ağzı |
| 1031 | Balık ağzı ucu | 0 uç yönü (ön), 1 ayna yönü (arka), 2 iki uç |
| 1032 / 1033 | Karşı boru Ø K / Birleşim açısı θ | |
| 1039 | Seçili delik no (1..8) | klasik wizard sayfa 2 |
| 1040–1046 | Seçili deliğin düzenleme alanı | tip, X, A, Y, L, W, R |
| 1100 + i·10 + c | Delik i (0..19), sütun c | c: 0 tip (0 yok, 1 yuvarlak, 2 oval, 3 pencere), 1 X (parça başından), 2 A (°), 3 Y ofset, 4 L (Ø), 5 W, 6 R |

## User LED
| LED | Anlam |
|---|---|
| 1000 / 1001 | yuvarlak / dikdörtgen |
| 1002 | X0 kontrol uyarısı |
| 1003 / 1004 | kenar kenar / tek seferde |
| 1005 / 1006 | çentik ayna / uç yönü |
| 1007 / 1008 | gönye / balık ağzı |
| 1009 / 1010 / 1011 | balık ağzı uç / ayna / iki uç |
| 1020–1027 | seçili delik 1–8 |
| 1030–1033 | delik tipi yok / yuvarlak / oval / pencere |
| 1034–1037 | delik yüzeyi 1–4 |

## UserLabel
| No | Kullanım |
|---|---|
| 1–3 | sayfa 2 ölçü başlıkları (tipe göre) |
| 11–18 | sayfa 2 delik listesi |
| 31–36 | Tube Studio wizard özet satırları |

## Makrolar
| M | Görev | Kullanan |
|---|---|---|
| M799 | varsayılan değerler | TubeCutting |
| M800 | G-kod üretimi + tubesim_data.js | ikisi |
| M801 | açı preset (P45/60/90) | TubeCutting |
| M802 | profil seçimi | TubeCutting |
| M803 / M804 | kaydet / yükle (tubecut.dat) | TubeCutting |
| M805 | dikdörtgen kesim şekli | TubeCutting |
| M806 | çentik yönü | TubeCutting |
| M807 | simülasyonu aç (Addons\TubeCutting\tubesim.html) | ikisi |
| M808 / M809 | uç şekli / balık ağzı ucu | TubeCutting |
| M810 / M811 / M812 | delik seç / tip / yüzey | TubeCutting |
| M820 | Tube Studio içe aktar (tubecut_config.txt) | TubeStudio |
| M821 | Tube Studio'yu aç (wizard_state.js yazar) | TubeStudio |
