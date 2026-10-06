# TubeMill — boru freze wizard'ı

Lazer kafası yerine **iş mili + freze takımı** ile boru kesme ve delme. Makine kinematiği lazerle aynıdır:
kafa X'te sabittir (yalnız Y ve Z hareket eder), ayna boruyu X ekseninde sürer ve A ekseninde döndürür.

| Parça | Dosya |
|---|---|
| G-kod üretimi | `macros/M900.bas` |
| Varsayılan değerler | `macros/M901.bas` |
| Seçim butonları | `macros/M902.bas` – `M906.bas` (profil, uç şekli, balık ağzı ucu, soğutma, delik yönü) |
| Kaydet / yükle | `macros/M907.bas` / `M908.bas` → `Addons\TubeMill\tubemill.dat` |
| Simülasyonu aç | `macros/M909.bas` → `Addons\TubeMill\tubemillsim.html` (kaynak: kök `sim/`, freze modu) |
| Wizard ekranları | `wizard/gen_page1.py`, `wizard/gen_page2.py`, `wizard/ui.py`, `wizard/build_set.py` |
| Testler | `tests/test_mill.py`, `tests/sim_check.js` (simülasyon sayfasını jsdom'da açar) |

Derleme çıktısı: `Mach3/Addons/TubeMill/` (TubeMill.set, 2 arka plan BMP, tubemillsim.html) ve `Mach3/macros/Mach3Mill/M900–M909.m1s`.
Mach3'te: Wizards → Pick Wizard → **TubeMill**.

## Makineyi hazırlama

1. **İş milini kafaya bağlayın.** Takım ekseni düşey (Z) olmalı.
2. **Y0:** takım ekseni boru merkezinin (döner eksenin) tam üstünde olmalı. Kenar bulucu veya iki yandan değdirme ile bulun.
   Y0 hatası yuvarlak boruda kesimi ve delikleri merkez dışına kaydırır.
3. **Z0:** A0 konumunda boru üst yüzeyi, **takım ucuyla** değdirme. Takımı değiştirince Z0'ı yeniden alın.
4. **X0:** boru ön ucu. X0'da takım merkezi boru ucunun tam üstündedir; takımın kenarıyla değdirirseniz takım yarıçapını ekleyin.
5. **A0:** dikdörtgende bir yüz tam yatay (Yüzey 1 üstte).
6. **Destek:** freze kuvveti lazerden çok büyüktür. Boruyu kesim noktasının yakınında **lünet / rulo destek** ile tutun.
   Uzun boşta kalan boru titrer, takım kırılır.
7. **İş mili:** M3 S… çıkışı iş milini açar. Elle açılan bir iş miliniz varsa, programdan önce elle açın; `G4` bekleme süresini yeterli verin.
8. **Talaş / soğutma:** alüminyumda sis (M7) veya alkol önerilir. Röle bağlı değilse M7/M8 bir şey yapmaz.

## Akış

1. Sayfa 1: profil, ölçüler, parça boyu ve adet, takım ve proses değerleri.
2. Sayfa 2 (*Delikler / uç >>*): uç şekli (gönye / balık ağzı) ve en çok 8 delik.
3. *Kod üret* (M900): G-kodu üretir, `tup_freze.tap` olarak yükler. Gereken boru boyu, en küçük X0 ve kesim süresi çıktıda görünür.
4. *Simülasyon* (M909): takımın yolunu 3B ve açınımda gösterir. Açınımda kesim izi takım çapı genişliğindedir.
   Takım malzemedeyken G0 ile yana giden bir hareket varsa kırmızı uyarı çıkar.
5. *Kaydet* / *Yükle* (M907 / M908): bütün değerler ve delikler `tubemill.dat` dosyasına.
6. **İlk çalıştırma: takım havada** (Z ofseti ile, örneğin +20 mm). Yolu izleyin, sonra gerçek kesim.

## Nasıl kesiyor

| İşlem | Yöntem |
|---|---|
| Yuvarlak uç kesimi | Takım radyal (Y0). A döner, her turda derinlik `ap` kadar artar (helisel giriş, dalma yok). Son tur tam derinlikte. G93 ters zaman. |
| Dikdörtgen uç kesimi | Yüz yüz. Takım borunun dışında havada iner, yüzü Y boyunca geçer (zikzak paso). Eğik kenarda yüz ucunda kenarı uzatmaz, köşe noktası etrafında rt yarıçaplı yayla döner. Eğik kesimde önce 0,05 mm ince paso. G94. |
| Yuvarlak / büyük delik | Kontur takım yarıçapı kadar içe kaydırılır, rampa ile iner (her turda `ap`), son tur tam derinlikte. |
| Delik Ø = takım Ø | Delme. Gagalama değeri > 0 ise gagalama. |
| Oval, W = takım Ø | Yiv: takım eksen boyunca git-gel, rampa ile iner. |
| Pencere | Köşeleri yuvarlatılmış kontur. R < takım yarıçapı ise köşe takım yarıçapında kalır. |

- **Takım telafisi** makroda hesaplanır (G41/G42 yok). Uç kesiminde takım merkezi parça kenarından `rt` uzakta, fire tarafında,
  kenarın normali boyunca (açınımda X ve çevre yönünde). Tasarım ölçüsü = net parça ölçüsü.
  Sanal işleme testi (`tests/test_vmachine.py`) çıkan parçanın boyunu, kenarlarını ve deliklerini ±0,07 mm doğrular.
- **Kesim izi = takım çapı.** 90° gönyede ardışık parçalar bir kesimi paylaşır (parça aralığı L + takım Ø).
  α ≠ 90° veya balık ağzında her parçanın iki ucu ayrı kesilir, araya fire girer.
- **Derinlik:** uç kesimi `t + taşma`. Dikdörtgende iç köşe yayı iki yüzden de kesilsin diye derinlik otomatik artar
  (`R − 0,707·(R − t) + taşma`, R > t ise). Yuvarlak boruda delik derinliği iç yüzeyin delik kenarındaki seviyesine göre hesaplanır.
- **Takım çapı düzeltmesi** (DRO 1529): ölçülen takım çapı − nominal çap. Takım aşınınca veya delik / parça ölçüsü
  sapınca kullanın (ör. Ø6 takım Ø5,95 ölçülürse −0,05). Bütün telafiler düzeltilmiş çapla hesaplanır.
- **Delik bitirme payı** (DRO 1525, en çok 2 mm): delik konturu önce bu pay kadar içeride kaba kesilir, sonra tam derinlikte
  bir tur bitirme pasosu nominal ölçüde geçer. Delik duvarı daha temiz ve ölçü daha doğru olur. Uç kesimlerinde
  bitirme pasosu yoktur: arka uç kesimi parçayı ayırır, ikinci tur mümkün değildir.
- **Delinme ilerlemesi:** et aşıldıktan sonra (son paso, delme sonu) ilerleme `F · Delinmede F % / 100` olur. Parça düşerken takımın yükü azalır.
- **Delik yönü:** tırmanma = delik içinde saat yönü tersi (M3 iş mili için), konvansiyonel = saat yönü.
  Makinenizde Y ekseni yönü tersse bu ikisi yer değiştirir.
- **Kesim sırası** lazerle aynı: boru ucuna en yakın parçadan aynaya doğru; her parçada ön uç → delikler → arka uç.

## Sınırlar

- Takım düşeydir: kesimin et içindeki yüzü radyaldir. Kalın ette eğik gönye yüzü tam düzlem olmaz.
  Dikdörtgen eğik kesimde yan yüzlerde düzlem yükseklikle kayar: makro takımı hiçbir yerde parçaya daldırmaz;
  dış yüzey kenarı tam (±cot α · 0,05), et içinde fazla et kalır (bir yan yüzde basamak ≤ cot α · ap, diğerinde ≤ cot α · t).
  Gönye birleşiminde iç köşe dolu kalabilir; gerekirse eğe ile alın.
- Çok dik balık ağzında (K ≈ boru çapı) kenarın eğrilik yarıçapı takım yarıçapından küçükse takım o bölgeye giremez.
- Yuvarlak boruda delik dik izdüşümdür (matkap tezgâhı gibi), lazer gibi çevreye sarılmaz.
  Delik kenarı iç yarıçapın içinde kalmalıdır (`|Y ofset| + W/2 < R − t − 0,5`).
- Dikdörtgende delik yüzeyin düz kısmında kalmalıdır (`|Y ofset| + W/2 ≤ yüz yarı genişliği − R`).
- Kesilen göbek (pencere içi) serbest kalır. Büyük pencerede göbeği bant veya mıknatısla tutun.
- Nokta sınırı: bir işlem en çok ~39000 nokta. Paso çok küçük veya delik çok derinse "Cok fazla nokta" hatası çıkar; paso derinliğini büyütün.
- Tube Studio bu wizard'ı desteklemez.
- Simülasyonda takım yolu takım ucunun izidir; kesilen malzeme (katı model) gösterilmez. Açınımdaki iz dış yüzeydedir.
- Makinede henüz denenmedi. İlk kullanımda kısa bir parçayla, havada deneyin.

## DRO / LED haritası

| DRO | Anlam | Not |
|---|---|---|
| 1500 | Profil | 0 yuvarlak, 1 dikdörtgen |
| 1501 | Çap D | yuvarlak |
| 1502 / 1503 | En A / Boy B | dikdörtgen |
| 1504 | Et kalınlığı t | kesim derinliği için gerekli |
| 1505 | Köşe radyüsü R | dış radyüs |
| 1506 / 1507 | α1 / α2 | α2 = 0 → α1 |
| 1508 | X0 | parça 1 ön kenarı (net) |
| 1509 / 1510 | Parça boyu L / adet | |
| 1511 / 1512 | Takım çapı / kesme boyu | kesme boyu < derinlik → hata |
| 1513 | Devir S | dev/dk |
| 1514 / 1515 | İlerleme F / dalma ilerlemesi | mm/dk |
| 1516 | Paso derinliği ap | |
| 1517 | Taşma | et altına iniş |
| 1518 | Delinmede F | % |
| 1519 | Güvenli mesafe | yüzeyden |
| 1520 | İş mili bekleme | s (G4 P) |
| 1521 | Soğutma | 0 yok, 1 M7, 2 M8 |
| 1522 | A segment açısı | yuvarlak kesimde adım |
| 1523 | Gagalama | 0 = tek seferde |
| 1524 | Delik yönü | 0 tırmanma, 1 konvansiyonel |
| 1525 | Delik bitirme payı | 0 = yok, en çok 2 mm |
| 1526 / 1527 / 1528 | (çıktı) gereken boru boyu / en küçük X0 / kesim süresi (dk) | M900 yazar |
| 1529 | Takım çapı düzeltmesi | ölçülen − nominal (±) |
| 1530 | Uç şekli | 0 gönye, 1 balık ağzı |
| 1531 | Balık ağzı ucu | 0 uç yönü, 1 ayna yönü, 2 iki uç |
| 1532 / 1533 | Karşı boru Ø K / birleşim açısı θ | |
| 1600 + i·10 + c | Delik i (0..7), sütun c | 0 tip (0 yok, 1 yuvarlak, 2 oval, 3 pencere), 1 X, 2 A (°), 3 Y ofset, 4 L (Ø), 5 W, 6 R |

| LED | Anlam |
|---|---|
| 1500 / 1501 | yuvarlak / dikdörtgen |
| 1502 | X0 uyarısı |
| 1503 / 1504 | gönye / balık ağzı |
| 1505 / 1506 / 1507 | balık ağzı uç / ayna / iki uç |
| 1508 / 1509 / 1510 | soğutma yok / M7 / M8 |
| 1511 / 1512 | tırmanma / konvansiyonel |

DRO ve LED numaraları lazer wizard'larıyla (1000–1297) çakışmaz; iki wizard aynı profilde birlikte durabilir.

## Geliştirme kuralları

- `MILL-LED` bloğu (LED tazeleme) M900–M906 ve M908'de **aynıdır** (girinti hariç). Değiştirirseniz hepsinde değiştirin; test kontrol eder.
- Makro dili kısıtları kök `CLAUDE.md` ile aynıdır (blok If, Sub/Function yok, cp1252).
- Her değişiklikten sonra: `python tools/build_all.py && python mill/tests/test_mill.py`.
- `tubemill.dat` biçimi: 1. satır sürüm (1), sonra DRO 1500–1533 ve 1600–1677, ×1000 tamsayı. Yeni DRO eklerseniz sürümü artırın.
