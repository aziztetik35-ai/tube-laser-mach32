# Geliştirme listesi

Durum: 2026-10. Öncelik: **Y** yüksek, **O** orta, **D** düşük.

## Bu turda düzeltilenler

| Konu | Düzeltme |
|---|---|
| M800 / M900: çok küçük A segment açısı veya paso → nokta dizisi taşıyordu (Mach3 çalışma hatası) | M800: A segment en az 0,1°. M900: en az 0,25°, gagalama en az 0,1 mm, nokta sayısı ön kontrolü ("Cok fazla nokta" hatası) |
| M800: 1 parçada parça boyu ≤ 0 kabul ediliyordu (arka kesim ön kesimin önüne düşüyordu) | Parça boyu her zaman zorunlu |
| M800: dikdörtgende yüzeyin düz kısmından taşan delik kabul ediliyordu (kesim köşede havada kalır) | Hata mesajı (Studio'da delik kırmızı görünür) |
| M800 / M900: geçersiz delik tipi (ör. 7) sessizce atlanıyordu | Hata mesajı |
| M900: takım boru çapından büyük olabiliyordu | Hata mesajı |
| install.py: yanlış profil adı yeni, boş bir profil klasörü açıyordu | Mach3.exe ve profil klasörü kontrolü, mevcut profilleri listeler |
| CI yoktu; `Mach3/` klasörü derlemeden geri kalabiliyordu | `.github/workflows/test.yml`: derleme + 3 test + `Mach3/` güncellik kontrolü |

## Makinede doğrulanması gerekenler

| Ö | Konu | Ne yapılmalı |
|---|---|---|
| Y | **TubeMill hiç denenmedi** | Havada deneme, sonra kısa parça. Y0, Z0 (takım ucuyla), delik yönü (tırmanma), iş mili / M7 / M8 çıkışları |
| Y | Tube Studio akışı (M820 / M821) | Shell ile tarayıcı açılıyor mu, `wizard_state.js` ve `tubecut_config.txt` yazılıyor / okunuyor mu |
| O | G93 ve A ekseni hız sınırı | Küçük çaplı boruda F yüksekse A ekseni limite takılır. Mach3'ün yavaşladığını ve kesimin düzgün kaldığını kontrol edin |

## Lazer (M800, TubeCutting, Tube Studio)

| Ö | Konu | Öneri |
|---|---|---|
| Y | Tek seferde modunda köşe yanığı (bilinen sınır) | Köşe geçiş bölgesi (A dönüşünü köşe öncesine yay) veya köşede güç düşürme (S değeri) |
| O | Ayna çarpışma kontrolü yok (`aynapay` tanımlı ama kullanılmıyor) | Boru boyu DRO'su ekle; son kesim + ayna payı > boru boyu ise hata |
| O | Klasik wizard 2. sayfası yalnız 8 delik gösterir (M800 20 keser) | Sayfalama (1–8 / 9–16 / 17–20) veya "Studio'da düzenle" uyarısı |
| O | Yuvarlak boruda delik konumu yalnız açı + Y ofset | Studio'da delik dizisi (n adet, adım, açı adımı) |
| D | Serbest kontur (polyline) delik yok | Studio'da çizim + M800'e kontur dosyasından okuma |
| D | Kerf telafisi yalnız parça aralığında | Delik konturunda yarım kerf içe kaydırma seçeneği |

## Freze (TubeMill, M900–M906)

| Ö | Konu | Öneri |
|---|---|---|
| Y | Kaydet / yükle yok (lazerde M803 / M804 var) | M907 / M908: DRO 1500–1677'yi `tubemill.dat` dosyasına ×1000 tamsayı ile yaz / oku |
| Y | Simülasyon yok (tubesim yalnız lazer) | M900 `tubemill_data.js` yazsın; tubesim'e takım çapı ve derinlik gösteren freze modu |
| O | Bitirme pasosu yok | Radyal bitirme payı DRO'su: kaba kontur + son tam derinlikte ince paso (daha iyi delik ölçüsü) |
| O | Takım çapı telafisi yalnız nominal | "Ölçülen takım çapı / aşınma" DRO'su; delik ölçüsü sapınca kullanıcı düzeltir |
| O | Kesilen göbek serbest düşüyor | Köprü (tab) seçeneği: son pasoda N adet köprü bırak |
| O | Pencere R < takım yarıçapı: köşe takım yarıçapında kalıyor, uyarı yok | Mesaj satırında uyarı |
| O | Süre tahmini G0 hareketlerini içermiyor | `GetParam("Velocities..")` ile hızlı hareket süresini ekle |
| D | Yuvarlak boruda delik dik izdüşüm | Radyal delik seçeneği (A ile sarılmış kontur, lazer gibi) |
| D | Dikdörtgende yalnız yüz yüz kesim | Köşede A dönerek tek seferde kesim (daha az giriş/çıkış) |
| D | 8 delik | 20 deliğe çıkarma (sayfa 2 tablosu kaydırma / ikinci tablo sayfası) |
| D | Tube Studio TubeMill'i bilmiyor | Studio'ya "freze" modu (takım çapı, izler, M900'ün JavaScript sürümü vb2js ile) |

## Altyapı

| Ö | Konu | Öneri |
|---|---|---|
| O | `Mach3/` klasöründe ~20 MB BMP; her ekran değişikliğinde depo büyür | Git LFS (`*.bmp`) veya ekranları seyrek değiştirmek |
| O | `Mach3/macros/Mach3Mill/` profil adı sabit | README'de belirtildi; istenirse build_all.py'ye `--profile` parametresi |
| D | install.py yedekten geri yükleme yapmıyor | `--geri-al <yedek klasörü>` seçeneği |
| D | WebGL görüntüsü testte yok | Görsel değişiklikte ekran görüntüsü (Playwright + Chromium ile otomatik alınabilir) |
