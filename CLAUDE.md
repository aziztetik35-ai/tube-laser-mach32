# CLAUDE.md — Tüp lazer (Mach3) projesi

Bu dosya Claude Code için proje hafızasıdır. Her değişiklikten önce oku; kurallar bölümüne uy.
Kullanıcı Türkçe konuşur, kısa ve öz cevap ister (gereksiz açıklama yok, yapılacak adımlar).

## Proje nedir

> Bu dosyanın çoğu lazer içindir. **TubeMill** (freze takımı ile kesim/delik) `mill/` altındadır; kuralları ve DRO haritası `mill/README.md`.

DIY tüp lazer kesim makinası (Mach3 + döner A ekseni). Üç parça:

1. **M800 makrosu** (`macros/M800.bas`) — bütün kesim G-kodunu üreten tek kaynak.
   Gönye, balık ağzı, delikler (20'ye kadar), tek seferde / kenar kenar dikdörtgen kesim, giriş çentiği.
2. **Mach3 wizard'ları** (MachScreen `.set` ekranları):
   - `TubeCutting` — klasik 2 sayfalı wizard (sayfa 1 ana parametreler, sayfa 2 delikler + uç şekli)
   - `TubeStudio` — sade wizard: "Studio'yu aç → İçe aktar → Kod üret"
3. **Tarayıcı uygulamaları** (tek dosya HTML, internet gerekmez):
   - `tubestudio.html` — konfigüratör: form + açınım üzerinde CAD tarzı delik çizimi + 3B önizleme.
     Önizleme, M800'ün **otomatik JavaScript'e çevrilmiş** halini çalıştırır (`studio/vb2js.py`).
   - `tubesim.html` — M800'ün yazdığı `tubesim_data.js`'i oynatan simülasyon. Aynı kaynak (`sim/`) `tubemillsim.html`'i de
     üretir: `TUBE_DATA.mode = "freze"` iken freze modu (takım, kesim izi, malzemede G0 uyarısı).

## Makine kinematiği ve koordinatlar (değiştirme!)

- Lazer kafası **X'te sabit**, yalnız Y ve Z hareket eder. Ayna boruyu **X ekseninde sürer** ve A ekseninde döndürür.
- **X0 = boru ön ucu** (değdirme). X arttıkça boru ucundan aynaya doğru gidilir.
- **Z0 = boru üst yüzeyi** (A0'da değdirme). M800 merkez tabanlı hesaplar, çıkışta `zofs` düşer
  (yuvarlak: R, dikdörtgen: B/2).
- **Y0** = döner eksenin düşey düzlemi. **A0** = dikdörtgende bir yüz yatay (Yüzey 1 üstte).
- Yüzey n = A = (n-1)·90° iken üstte kalan yüz. Çevre boyunca +s yönü = makine +Y yönü (her yüzde).
- **Kesim sırası:** boru ucuna en yakın parçadan aynaya doğru. Her parça için: ön uç → delikler → arka uç
  (parça arka uç kesimiyle düşer; delikler parça ayrılmadan kesilir).
- Gönye düzlemi: dikdörtgende `x = xref + cot(α)·u`, yuvarlakta `x = xref + cot(α)·v` (v = R·cos φ).
- Balık ağzı: `x = xref + w·cot θ + sg·(Rb − √(Rb² − n²))/sin θ` (w eğim koordinatı, n diğer koordinat; sg: +1 arka uç, −1 ön uç).
- `ayri = 1` (balık ağzı veya α1 ≠ α2) → her parçanın iki ucu ayrı kesilir, araya otomatik fire girer.
  `ayri = 0` → ardışık parçalar aynı kesim çizgisini paylaşır (ilk kesim boru ucunu kırpar; adet+1 kesim).
- **Kerf telafisi (M800):** xL/xR parçanın net kenarı; uç kesim çizgisi kerf/2 fire tarafında, delik konturu kerf/2 içeride.
  X0 = 1. parçanın net ön kenarı. Sanal işleme testi parça boyu, kenar ve delik ölçüsünü ±0,07 mm doğrular.
- Kenar kenar + eğik uç (dikdörtgen): dik ışın yan yüzde eti sabit X'te keser; eğik düzlem et içinde cot(α)·t kayar.
  Bu kerften büyükse köşede köprü kalır (sanal işlemede görülür) → M800 uyarır, tek seferde önerilir.
- G-kod: G93 ters zaman besleme, her kesim satırı **G1** ile başlar (G0 modal kalırsa kesim rapid olur — test bunu yakalar).

DRO / LED / etiket haritası: `docs/DRO_MAP.md`.

## Dizinler

```
macros/              *.bas  — makro KAYNAKLARI (UTF-8, LF). Derleme cp1252 + CRLF .m1s üretir.
wizard/common/       setlib.py — MachScreen .set okuyucu
wizard/tubecutting/  gen_page1.py, gen_page2.py (arka plan BMP + yerleşim CSV), build_set.py (.set)
wizard/tubestudio/   gen_bg.py, build_set.py
reference/           MachScreen örnek .set dosyaları (kayıt formatı bunlardan klonlanır) — SİLME
sim/                 core.js (G-kod ayrıştırma, örnekleme, açınım), app.js, shell.html, build.py
studio/              vb2js.py, viewer.js, editor.js, studio.js, shell.html, build.py  (m800.js ÜRETİLİR)
vendor/              three.js r128 + OrbitControls (MIT), DejaVu fontları
tools/               build_all.py, install.py, vbrun.py (VB alt kümesini Python'da çalıştırır), vmachine.py (sanal işleme)
tests/               test_macros.py, studio_ui.test.js
mill/                TubeMill (freze): macros/M900-M909.bas, wizard/ (ui, gen_page1/2, build_set), tests/test_mill.py
dist/                derleme çıktısı (git'e girmez)
Mach3/               dist/Mach3'ün git'te tutulan kopyası (build_all.py yazar; elle düzenleme, build sonrası commit et)
```

## Komutlar

```bash
npm install                       # yalnız test için (jsdom)
python tools/build_all.py         # her şeyi dist/Mach3/ altına derler
python tests/test_macros.py       # makro testleri (sözdizimi, Python==JS, geometri, kaydet/yükle/içe aktar)
node tests/studio_ui.test.js      # Studio arayüz testi (build sonrası)
python mill/tests/test_mill.py    # TubeMill testleri (takım telafisi, derinlik, delik, kaydet/yükle, simülasyon sayfaları; build sonrası)
python tests/test_vmachine.py     # SANAL İŞLEME: G-kod kinematikle çalışır, et kaldırılır, çıkan parça ölçülür (pip install numpy scipy, ~3 dk)
python tools/install.py --mach3 "C:\Mach3" --profile Mach3Mill   # Mach3'e kur (yedek alır), --dry-run ile dene
```

**Her değişiklikten sonra:** `python tools/build_all.py && python tests/test_macros.py && node tests/studio_ui.test.js && python mill/tests/test_mill.py`.
Kesim geometrisi (M800/M900) değiştiyse ayrıca `python tests/test_vmachine.py` (gerçek parça ölçüsü ±0,07 mm).
Testler geçmeden "bitti" deme. Build `Mach3/` klasörünü günceller → onu da commit et. Geometri değişikliğinde yeni bir test durumu ekle.

## ALTIN KURALLAR

1. **M800 tek doğruluk kaynağıdır.** Kesim geometrisini JavaScript'te ayrıca yazma; Studio önizlemesi
   `vb2js.py` ile M800'den üretilir. `studio/m800.js`'i elle düzenleme (build onu yeniden yazar).
2. **Makro dili kısıtları (Mach3 Cypress Enable VB):**
   - Tek satır `If ... Then x` YOK → her zaman blok `If ... Then / End If`.
   - `While/Wend`, `Do/Loop`, `Select Case`, `Sub`, `Function` YOK (kullanıcı tanımlı fonksiyon derleme hatası verir).
     Tekrarlanan kod blokları kopyalanır (bkz. kural 4).
   - Kullanılabilir: `For/Next` (Step −1 dahil), `Exit For`, `Dim a(N)` diziler, `Int Abs Sqr Sin Cos Tan Atn`,
     `InStr Left Mid Right Val Chr`, `Open/Print #/Line Input #/Input #/Close`, `Dir`, `Shell`.
   - `Err` değişken adı yasak (iç nesne). `Mod` operatörü var; değişken adı olarak `mod` kullanma.
   - Sayı → metin: `"X" & deger` ondalık NOKTA üretir (G-kod için doğru). Dosyaya sayı yazarken locale riski
     varsa ×1000 tamsayı yaz (M803'teki gibi). Okurken `Val()` kullan.
   - Kaynak `.bas` UTF-8'dir ama içerik **cp1252'ye sığmalı**: ı ş ğ İ Ş Ğ YOK (ç ö ü Ç Ö Ü Ø × · ° olur).
     Mesajlarda "basin, degeri" gibi yaz. Build cp1252 dışı karakterde hata verir.
   - `vbrun.py` / `vb2js.py` yalnız bu alt kümeyi destekler; yeni bir VB yapısı kullanırsan iki çeviriciyi de güncelle.
3. **Mach3 API:** `GetUserDRO/SetUserDRO`, `SetUserLED`, `SetUserLabel(n, metin)` (ekrandaki `UserLabelN` etiketi),
   `Code "..."` (teach file'a yaz), `OpenTeachFile/CloseTeachFile/LoadTeachFile`, `Message`, `SaveWizard()`,
   `DoOEMButton(n)`, `GetParam("VelocitiesX")` (birim/saniye), `GetMainFolder()`, `Param1()` (M-kod P değeri).
4. **Kopyalanmış ortak bloklar** (değiştirirsen HEPSİNDE aynı değiştir):
   - FLUSH (düzenleme alanı 1040–1046 → seçili delik): M800, M803, M810, M811, M812, M821
   - LOAD (seçili delik → düzenleme alanı): M804, M810, M820
   - REFRESH (LED'ler, ölçü başlıkları UserLabel 1–3, delik listesi 11–18): M799, M800, M804, M810, M811, M812, M820
   - LED tazeleme (1000–1011): M804, M820 · Özet (UserLabel 31–36): M820, M821
   - MILL-LED (TubeMill LED'leri 1500–1512): M900–M906, M908 (test aynılığını kontrol eder)
5. **Klasik wizard'ın 2. sayfası yalnız ilk 8 deliği** gösterir/düzenler; M800 20 deliği keser (DRO 1100–1297).
6. **Kullanıcı verisini ezme:** `tubecut.dat`, `tubecut_config.txt`, `wizard_state.js`, `tubesim_data.js`, `tubemill.dat`, `tubemill_data.js` makinede üretilir; repoya koyma.
7. Güvenlik: kesim sırasını, X0/Z0 referansını veya G1/G93 düzenini değiştiren her şeyi kullanıcıya açıkça söyle
   ve ilk denemenin **lazer kapalı (S0)** yapılmasını hatırlat.

## MachScreen .set formatı (wizard ekranları)

İkili format, `reference/` örneklerinden çözüldü (`wizard/common/setlib.py` okur):
- Başlık: `int32 kayıt_sayısı`, ardından kayıtlar, sonda 44 bayt sabit renk bloğu (`TRAILER`).
- Kayıt: `int32 fonksiyon, int32 tür, int32 sayfa`, 3 dize (başlık, G-kod/script, resim), 8 bayt, dize (etiket metni),
  `int32 std, int32 oem`, 12 bayt, dize (format), `int32 0`, `int32×4 dikdörtgen (sol, üst, sağ, alt)`.
  Dizeler 1 bayt uzunluk önekli (≥255 ise 0xFF + uint16).
- Türler: 1 DRO (fonksiyon 12, OEM kodu = DRO no), 3 arka plan, 4 buton, 6 LED (fonksiyon 56), 7 etiket, 11 toolpath.
- Buton fonksiyonu: 33 = "Std Execute G-Code" (kod `M810 P1\r\n`), 34 = Basic script, 32 = OEM kodu.
  OEM 231 = wizard'dan çık, OEM n (1..9) = n. sayfaya git (script `SetPage()` wizard'da ÇALIŞMADI).
- Etiket metni `Error` → durum satırı; `UserLabelN` → `SetUserLabel(N, ..)` ile değişir;
  `Desc ...` / `Author ...` → Pick Wizard listesindeki açıklama/yazar (ekran dışına konur).
- Koordinatlar 1024×768 mantıksal alandadır; Mach3 ekrana ölçekler. Arka plan BMP 1920×1080 çizilir
  (`Px` sınıfı ölçekler). Buton başlıkları cp1252 (ı ş ğ yok → "Varsayilan", "Kapat", "Iki uç").
- Mach3 arka plan resmini açılışta önbelleğe alır → değişiklikten sonra **Mach3'ü yeniden başlat**.
- Yeni kontrol eklemek: `gen_page*.py` içinde `button()/row()/ledsock()` çağır (CSV'ye yazar), `build_set.py` CSV'den kayıt üretir.

## Tube Studio mimarisi

- `studio.js`: durum `C` (ana DRO'lar) + `H` (delikler `{tip,x,a,y,l,w,r}`), form, `compute()` → `runM800()`.
- `editor.js`: açınım editörü. Koordinat: x = parça başından, t = çevre konumu (dikdörtgende yüzey bantları,
  yuvarlakta dikiş A=180° → A0 ortada). Yakalama, ortho, geri al/yinele, çoğalt, L tutamağı.
  Parça uç eğrileri M800 çıktısından (`makeOutline`) çizilir; M800 hata mesajındaki "Delik N" kırmızı gösterilir.
- `viewer.js`: three.js 3B + açınım + animasyon (taşıyıcı X'te kayar, boru A'da döner, kafa sabit). Eksen hız limitleri
  hesaba katılır (mor = limite takılan kesim).
- Wizard'a gönder: File System Access API ile `Addons\TubeStudio\tubecut_config.txt` yazar
  (`TUBESTUDIO 1` / `DRO=değer` satırları / `END`); desteklenmezse indirir. M820 okur.
- M821 güncel DRO'ları `wizard_state.js` olarak yazar; Studio açılışta bunu yükler.

## Bilinen sınırlar / yapılacaklar

Tam liste ve öncelikler: `docs/GELISTIRME.md` (yeni bir sınır bulursan oraya ekle).

- Tek seferde modunda köşelerde A ekseni 90° dönerken yüzey yolu kısa → eksen limiti nedeniyle yavaşlama ve yanık.
  Önerilen çözüm (henüz yok): köşe geçiş bölgesi (A dönüşünü köşe öncesine yay) veya köşede güç düşürme.
- Makinede çalıştığı görülenler: wizard ekranları, M800 kod üretimi, SetUserLabel listesi, OEM sayfa geçişi.
  Makinede henüz doğrulanmayanlar: Tube Studio akışı (M820/M821: Shell, wizard_state.js / tubecut_config.txt dosya I/O,
  tarayıcının klasöre yazma izni). Yeni bir Mach3 API kullanırsan kullanıcıdan makinede denemesini iste.
- WebGL görüntüsü testte doğrulanamaz (jsdom); görsel değişikliklerde kullanıcıdan ekran görüntüsü iste.
