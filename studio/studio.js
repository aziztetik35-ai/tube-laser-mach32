// ===== Tube Studio – konfigürasyon arayüzü =====
(function () {
  var $ = function (id) { return document.getElementById(id); };

  // ---------- durum (DRO numaralarıyla, M800 ile aynı) ----------
  var DEF = { 1000: 0, 1001: 50, 1002: 40, 1003: 40, 1004: 2, 1005: 0, 1006: 45, 1007: 45, 1008: 100, 1009: 1200, 1010: 0.3,
              1011: 0.2, 1012: 25, 1013: 1, 1014: 800, 1015: 2, 1016: 2, 1017: 200, 1018: 1, 1019: 0, 1022: 0, 1023: 1,
              1030: 0, 1031: 0, 1032: 60, 1033: 90 };
  var MACH = { vx: 3000, vy: 3000, vz: 3000, va: 10000 };
  var C = {}, H = [];   // C: ana DRO'lar, H: delikler [{tip,x,a,y,l,w,r}]
  function reset() {
    C = Object.assign({}, DEF); H = [];
    if (typeof WIZARD_STATE !== "undefined") {
      for (var k in DEF) if (WIZARD_STATE[k] !== undefined) C[k] = +WIZARD_STATE[k];
      for (var i = 0; i < 20; i++) {
        var b = 1100 + i * 10, t = Math.round(+WIZARD_STATE[b] || 0);
        if (t >= 1 && t <= 3) H.push({ tip: t, x: +WIZARD_STATE[b + 1] || 0, a: +WIZARD_STATE[b + 2] || 0, y: +WIZARD_STATE[b + 3] || 0,
                                       l: +WIZARD_STATE[b + 4] || 0, w: +WIZARD_STATE[b + 5] || 0, r: +WIZARD_STATE[b + 6] || 0 });
      }
      ["vx", "vy", "vz", "va"].forEach(function (k) { if (+WIZARD_STATE[k] > 0) MACH[k] = +WIZARD_STATE[k]; });
    }
  }
  function toDRO() {
    var d = Object.assign({}, C);
    for (var i = 0; i < 20; i++) {
      var b = 1100 + i * 10, h = H[i] || { tip: 0, x: 0, a: 0, y: 0, l: 0, w: 0, r: 0 };
      d[b] = h.tip; d[b + 1] = h.x; d[b + 2] = h.a; d[b + 3] = h.y; d[b + 4] = h.l; d[b + 5] = h.w; d[b + 6] = h.r;
    }
    d[1039] = 1;                                   // düzenleme alanı = 1. delik (M800 başta bunu saklar)
    for (var c = 0; c < 7; c++) d[1040 + c] = d[1100 + c];
    return d;
  }

  // ---------- form tanımı ----------
  var isRect = function () { return +C[1000] === 1; };
  var SECTIONS = [
    { title: "Profil", items: [
      { seg: 1000, opts: [["Yuvarlak", 0], ["Dikdörtgen", 1]] },
      { n: 1001, label: "Çap  D", unit: "mm", show: function () { return !isRect(); } },
      { n: 1002, label: "Genişlik  A", unit: "mm", show: isRect },
      { n: 1003, label: "Yükseklik  B", unit: "mm", show: isRect },
      { n: 1005, label: "Köşe radyüsü  R", unit: "mm", show: isRect },
      { n: 1004, label: "Et kalınlığı  t", unit: "mm" } ] },
    { title: "Kesim", items: [
      { n: 1008, label: "Boru ucundan  X0", unit: "mm", hint: "Boru ucu değdirme ile X0 = 0" },
      { n: 1017, label: "Parça boyu  L", unit: "mm" },
      { n: 1018, label: "Parça adedi", unit: "ad", int: true },
      { n: 1006, label: "Başlangıç açısı  α1", unit: "°", chips: [45, 60, 90] },
      { n: 1007, label: "Bitiş açısı  α2", unit: "°", chips: [45, 60, 90] },
      { n: 1011, label: "Kerf", unit: "mm" },
      { seg: 1019, label: "Dikdörtgen kesim şekli", opts: [["Kenar kenar", 0], ["Tek seferde", 1]], show: isRect } ] },
    { title: "Uç şekli", items: [
      { seg: 1030, opts: [["Gönye", 0], ["Balık ağzı", 1]] },
      { seg: 1031, label: "Balık ağzı hangi uçta", opts: [["Uç yönü", 0], ["Ayna yönü", 1], ["İki uç", 2]], show: function () { return +C[1030] === 1; } },
      { n: 1032, label: "Karşı boru  Ø K", unit: "mm", show: function () { return +C[1030] === 1; } },
      { n: 1033, label: "Birleşim açısı  θ", unit: "°", show: function () { return +C[1030] === 1; } } ] },
    { title: "Delikler", holes: true },
    { title: "Proses", items: [
      { n: 1009, label: "Kesim hızı  F", unit: "mm/dk" },
      { n: 1014, label: "Lazer gücü  S", unit: "S" },
      { n: 1010, label: "Pierce süresi", unit: "s" },
      { n: 1013, label: "Kesim yüksekliği", unit: "mm" },
      { n: 1012, label: "Güvenli mesafe", unit: "mm" },
      { n: 1016, label: "A segment açısı", unit: "°" },
      { n: 1015, label: "Lead-in", unit: "mm" },
      { n: 1022, label: "Giriş çentiği", unit: "mm", hint: "0 = yok" },
      { seg: 1023, label: "Çentik yönü", opts: [["Ayna yönü", 0], ["Uç yönü", 1]], show: function () { return +C[1022] > 0; } } ] },
    { title: "Makine (simülasyon için eksen hızları)", collapsed: true, items: [
      { m: "vx", label: "X max hız", unit: "mm/dk" }, { m: "vy", label: "Y max hız", unit: "mm/dk" },
      { m: "vz", label: "Z max hız", unit: "mm/dk" }, { m: "va", label: "A max hız", unit: "°/dk" } ] }
  ];

  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) { if (k === "class") e.className = attrs[k]; else if (k.slice(0, 2) === "on") e[k] = attrs[k]; else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { if (c != null) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function numInput(get, set, int) {
    var inp = h("input", { type: "number", step: int ? "1" : "any", inputmode: "decimal" });
    inp.value = get();
    inp.oninput = function () { var v = parseFloat(String(inp.value).replace(",", ".")); if (!isNaN(v)) { set(int ? Math.round(v) : v); schedule(); } };
    inp.onchange = function () { render(); };
    return inp;
  }
  function segCtrl(cur, opts, onpick) {
    return h("div", { class: "seg" }, opts.map(function (o) {
      return h("button", { class: +cur === o[1] ? "on" : "", onclick: function () { onpick(o[1]); } }, [o[0]]);
    }));
  }
  function row(label, ctrl, unit, hint) {
    return h("div", { class: "row" }, [h("label", {}, [label, hint ? h("small", {}, [hint]) : null]), h("div", { class: "ctl" }, [ctrl, unit ? h("span", { class: "unit" }, [unit]) : null])]);
  }

  var open = {};
  var selHole = -1, editor = null;
  function render() {
    var root = $("form"); var scroll = root.scrollTop; root.innerHTML = "";
    SECTIONS.forEach(function (sec, si) {
      var collapsed = open[si] === undefined ? !!sec.collapsed : !open[si];
      var body = h("div", { class: "body" });
      var head = h("button", { class: "sechead", onclick: function () { open[si] = collapsed; render(); } },
                   [h("span", { class: "num" }, [String(si + 1)]), sec.title, h("span", { class: "chev" }, [collapsed ? "▸" : "▾"])]);
      if (!collapsed) {
        if (sec.holes) renderHoles(body);
        (sec.items || []).forEach(function (it) {
          if (it.show && !it.show()) return;
          if (it.seg !== undefined) {
            var s = segCtrl(C[it.seg], it.opts, function (v) { C[it.seg] = v; render(); schedule(true); });
            body.appendChild(it.label ? row(it.label, s) : h("div", { class: "row full" }, [s]));
          } else if (it.m) {
            body.appendChild(row(it.label, numInput(function () { return MACH[it.m]; }, function (v) { MACH[it.m] = v; }), it.unit));
          } else {
            var ctl = numInput(function () { return C[it.n]; }, function (v) { C[it.n] = v; }, it.int);
            var wrap = h("div", { class: "withchips" }, [ctl].concat((it.chips || []).map(function (c) {
              return h("button", { class: "chip" + (+C[it.n] === c ? " on" : ""), onclick: function () { C[it.n] = c; render(); schedule(true); } }, [c + "°"]);
            })));
            body.appendChild(row(it.label, it.chips ? wrap : ctl, it.unit, it.hint));
          }
        });
      }
      root.appendChild(h("section", { class: collapsed ? "collapsed" : "" }, [head, body]));
    });
    root.scrollTop = scroll;
  }

  var HTYPES = [["Yuvarlak", 1], ["Oval", 2], ["Pencere", 3]];
  function renderHoles(body) {
    if (!H.length) body.appendChild(h("p", { class: "empty" }, ["Delik yok. Eklemek için aşağıdaki butonu kullanın."]));
    H.forEach(function (ho, i) {
      var card = h("div", { class: "hole" + (i === selHole ? " sel" : ""), id: "hole_" + i, onclick: function (e) {
        if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") return;
        selHole = i; editor && editor.select(i); render();
      } });
      card.appendChild(h("div", { class: "hhead" }, [h("b", {}, ["Delik " + (i + 1)]),
        segCtrl(ho.tip, HTYPES, function (v) {
          ho.tip = v;
          if (v === 1 && !(ho.l > 0)) ho.l = 10;
          if (v === 2) { if (!(ho.l > 0)) ho.l = 20; if (!(ho.w > 0)) ho.w = 8; }
          if (v === 3) { if (!(ho.l > 0)) ho.l = 30; if (!(ho.w > 0)) ho.w = 15; }
          render(); schedule(true);
        }),
        h("button", { class: "del", title: "Deliği sil", onclick: function () { H.splice(i, 1); render(); schedule(true); } }, ["×"])]));
      card.appendChild(row("Parça başından", numInput(function () { return ho.x; }, function (v) { ho.x = v; }), "mm", "Parçanın boru ucu tarafından"));
      if (isRect()) {
        var face = Math.round((((ho.a % 360) + 360) % 360) / 90) % 4;
        card.appendChild(row("Yüzey", segCtrl(face, [["1", 0], ["2", 1], ["3", 2], ["4", 3]], function (v) { ho.a = v * 90; render(); schedule(true); })));
      } else {
        card.appendChild(row("Açı", numInput(function () { return ho.a; }, function (v) { ho.a = v; }), "°"));
      }
      card.appendChild(row("Ortadan kaydırma", numInput(function () { return ho.y; }, function (v) { ho.y = v; }), "mm"));
      if (ho.tip === 1) card.appendChild(row("Çap", numInput(function () { return ho.l; }, function (v) { ho.l = v; }), "mm"));
      else {
        card.appendChild(row("Boy (eksen yönü)", numInput(function () { return ho.l; }, function (v) { ho.l = v; }), "mm"));
        card.appendChild(row("En (çevre yönü)", numInput(function () { return ho.w; }, function (v) { ho.w = v; }), "mm"));
        if (ho.tip === 3) card.appendChild(row("Köşe radyüsü", numInput(function () { return ho.r; }, function (v) { ho.r = v; }), "mm"));
      }
      body.appendChild(card);
    });
    if (H.length < 20) body.appendChild(h("button", { class: "add", onclick: function () {
      var last = H[H.length - 1];
      H.push({ tip: 1, x: last ? last.x + 50 : 50, a: last ? last.a : 0, y: 0, l: 10, w: 0, r: 0 }); render(); schedule(true);
    } }, ["+ Delik ekle"]));
    else body.appendChild(h("p", { class: "empty" }, ["En fazla 20 delik."]));
  }

  // ---------- hesap + önizleme ----------
  var viewer = createTubeViewer({ stage: $("stage"), view3d: $("view3d"), canvas: $("unfold"),
    el: { time: $("time"), pos: $("pos"), laser: $("laser"), line: $("line"), scrub: $("scrub"), play: $("play") } });
  var timer = null, last = null, outline = null, badMap = {};
  // parça 1'in ön/arka uç kesim eğrileri (parça koordinatında: x - X0, çevre konumu t)
  function makeOutline(G, D) {
    var prof = SIMCORE.profileOf(D), per = SIMCORE.buildPerimeter(prof.a, prof.b, prof.r);
    var parsed = SIMCORE.parseGcode(G), smp = SIMCORE.sampleMoves(parsed.moves, (+D.stof || 0) - (+D.zofs || 0));
    var marks = [];
    G.forEach(function (l, i) { if (/^\(parca 1 - (gonye|balik agzi)/.test(l)) marks.push(i + 1); });
    var shift = +D.tip === 0 ? per.P / 2 : 0, x0 = +D.x0 || 0;
    function group(k) {
      var a = marks[k], b = G.length + 1, out = [];
      if (a == null) return out;
      for (var j = a; j < G.length; j++) if (/^\(parca /.test(G[j])) { b = j + 1; break; }
      smp.cut.forEach(function (c) {
        var ln = parsed.moves[c.move].line; if (ln <= a || ln >= b) return;
        var q = SIMCORE.sOf(per, c.p1.u, c.p1.v); if (q.d > 0.5) return;
        out.push([c.p1.x - x0, (q.s + shift) % per.P]);
      });
      return out;
    }
    return { front: group(0), back: group(1) };
  }
  function schedule(now) { clearTimeout(timer); timer = setTimeout(compute, now ? 0 : 300); }
  function fmtT(s) { s = Math.round(Math.max(0, s)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function compute() {
    var dro = toDRO();
    var r = runM800(dro, { VelocitiesX: MACH.vx / 60, VelocitiesY: MACH.vy / 60, VelocitiesZ: MACH.vz / 60, VelocitiesA: MACH.va / 60 });
    var msg = r.error ? "Hesap hatası: " + r.error : (r.msgs[r.msgs.length - 1] || "");
    var bad = !!r.error || /^HATA/.test(msg) || !r.gcode.length;
    $("status").className = bad ? "bad" : "ok";
    $("status").textContent = bad ? msg.replace(/^HATA:\s*/, "") : "Hazır";
    $("send").disabled = false;
    badMap = {};
    var mh = /Delik (\d+)/.exec(msg); if (bad && mh) badMap[+mh[1] - 1] = true;
    if (editor) editor.draw();
    if (bad) { $("msgbar").textContent = msg; $("msgbar").className = "err"; return; }
    $("msgbar").textContent = ""; $("msgbar").className = "";
    var tip = +C[1000];
    var D = { tip: tip, D: C[1001], A: C[1002], B: C[1003], R: C[1005], t: C[1004], beta: C[1006], beta2: C[1007], x0: C[1008], L: C[1017],
              adet: C[1018], kerf: C[1011], stof: C[1013], sekil: C[1019], cent: C[1022], ctaraf: C[1023], hiz: C[1009],
              zofs: tip === 0 ? C[1001] / 2 : C[1003] / 2, btip: C[1030], buc: C[1031], bcap: C[1032], bteta: C[1033],
              vx: MACH.vx, vy: MACH.vy, vz: MACH.vz, va: MACH.va };
    var res = viewer.load(D, r.gcode);
    outline = makeOutline(r.gcode, D);
    if (editor) editor.draw();
    last = { dro: dro, gcode: r.gcode, set: r.set };
    var st = res.stats, holes = r.gcode.filter(function (l) { return /delik/.test(l); }).length;
    var parts = (msg.match(/(\d+) parca/) || [])[1] || "-";
    $("stats").innerHTML = [
      ["Parça", parts], ["Delik", holes], ["Delme", st.pierces], ["Kesim yolu", Math.round(st.cutLen) + " mm"],
      ["Kesim süresi", fmtT(st.cutTime)], ["Toplam süre", fmtT(st.total)],
      ["Gereken boru", (r.set[1020] != null ? Math.round(r.set[1020]) : "-") + " mm"], ["En küçük X0", (r.set[1021] != null ? r.set[1021] : "-") + " mm"]
    ].map(function (x) { return "<div><span>" + x[0] + "</span><b>" + x[1] + "</b></div>"; }).join("");
    if (st.extra > 0.3) { $("msgbar").textContent = "Köşelerde eksen hız limiti nedeniyle yavaşlama: +" + st.extra.toFixed(1) + " s (mor bölgeler, yanık riski)."; $("msgbar").className = "warn"; }
    $("gcode").value = r.gcode.length > 4000 ? r.gcode.slice(0, 4000).join("\n") + "\n… (" + r.gcode.length + " satır)" : r.gcode.join("\n");
  }

  // ---------- wizard'a gönder ----------
  function configText() {
    var d = toDRO(), lines = ["TUBESTUDIO 1"];
    Object.keys(d).map(Number).sort(function (a, b) { return a - b; }).forEach(function (n) {
      if ((n >= 1000 && n <= 1033 && n !== 1020 && n !== 1021) || (n >= 1100 && n <= 1297)) lines.push(n + "=" + (+d[n]));
    });
    lines.push("END");
    return lines.join("\r\n") + "\r\n";
  }
  function idb() {
    return new Promise(function (res, rej) {
      var r = indexedDB.open("tubestudio", 1);
      r.onupgradeneeded = function () { r.result.createObjectStore("kv"); };
      r.onsuccess = function () { res(r.result); }; r.onerror = function () { rej(r.error); };
    });
  }
  function kv(key, val) {
    return idb().then(function (db) {
      return new Promise(function (res, rej) {
        var tx = db.transaction("kv", val === undefined ? "readonly" : "readwrite"), s = tx.objectStore("kv");
        var q = val === undefined ? s.get(key) : s.put(val, key);
        q.onsuccess = function () { res(q.result); }; q.onerror = function () { rej(q.error); };
      });
    });
  }
  function toast(t, bad) { var e = $("toast"); e.textContent = t; e.className = "show" + (bad ? " bad" : ""); clearTimeout(e._t); e._t = setTimeout(function () { e.className = ""; }, 6000); }
  function download(name, text) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/plain" })); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  async function pickDir() {
    var dir = await window.showDirectoryPicker({ id: "tubestudio", mode: "readwrite" });
    await kv("dir", dir); return dir;
  }
  async function send(force) {
    var txt = configText();
    if (!window.showDirectoryPicker) {
      download("tubecut_config.txt", txt);
      toast("Tarayıcı klasöre yazamıyor: dosya indirildi. Mach3\\Addons\\TubeStudio klasörüne kopyalayıp İçe aktar'a basın.");
      return;
    }
    try {
      var dir = force ? null : await kv("dir").catch(function () { return null; });
      if (!dir) { toast("Mach3\\Addons\\TubeStudio klasörünü seçin (bir kez)."); dir = await pickDir(); }
      if ((await dir.queryPermission({ mode: "readwrite" })) !== "granted" &&
          (await dir.requestPermission({ mode: "readwrite" })) !== "granted") throw new Error("Klasöre yazma izni verilmedi");
      var fh = await dir.getFileHandle("tubecut_config.txt", { create: true });
      var w = await fh.createWritable(); await w.write(txt); await w.close();
      $("dirname").textContent = dir.name;
      toast("Gönderildi → " + dir.name + "\\tubecut_config.txt  ·  Mach3'te İçe aktar'a basın.");
    } catch (e) {
      if (e && e.name === "AbortError") return;
      download("tubecut_config.txt", txt);
      toast("Klasöre yazılamadı (" + (e.message || e) + "). Dosya indirildi; Addons\\TubeStudio'ya kopyalayın.", true);
    }
  }
  $("send").onclick = function () { send(false); };
  $("chdir").onclick = function (e) { e.preventDefault(); send(true); };
  kv("dir").then(function (d) { if (d) $("dirname").textContent = d.name; }).catch(function () {});

  // ---------- iş kaydet / aç ----------
  $("saveJob").onclick = function () { download("tube_is.json", JSON.stringify({ C: C, H: H, MACH: MACH }, null, 1)); };
  $("openJob").onclick = function () { $("jobfile").click(); };
  $("jobfile").onchange = function () {
    var f = this.files[0]; if (!f) return;
    f.text().then(function (t) {
      var j = JSON.parse(t); C = Object.assign({}, DEF, j.C || {}); H = j.H || []; MACH = Object.assign(MACH, j.MACH || {});
      render(); schedule(true); toast("İş açıldı: " + f.name);
    }).catch(function (e) { toast("Dosya okunamadı: " + e.message, true); });
    this.value = "";
  };
  $("resetAll").onclick = function () { if (confirm("Tüm değerler wizard'daki (veya varsayılan) değerlere dönsün mü?")) { reset(); render(); schedule(true); } };
  $("dlTap").onclick = function () { if (last) download("tup_kesim.tap", last.gcode.join("\r\n") + "\r\n"); };

  // ---------- önizleme kontrolleri ----------
  var curTab = "draw";
  function setTab(t) {
    curTab = t;
    ["draw", "3d", "unfold", "gcode"].forEach(function (k) { $("tab_" + k).classList.toggle("active", k === t); });
    $("gcodebox").style.display = t === "gcode" ? "block" : "none";
    $("hud").style.display = (t === "3d" || t === "unfold") ? "block" : "none";
    $("drawcv").style.display = t === "draw" ? "block" : "none";
    $("drawbar").style.display = t === "draw" ? "flex" : "none";
    $("playbar").style.visibility = t === "draw" ? "hidden" : "visible";
    viewer.setTab(t === "3d" || t === "unfold" ? t : "none");
    if (t === "draw") { editor.refit(); }
  }
  $("tab_draw").onclick = function () { setTab("draw"); };
  $("tab_3d").onclick = function () { setTab("3d"); };
  $("tab_unfold").onclick = function () { setTab("unfold"); };
  $("tab_gcode").onclick = function () { setTab("gcode"); };
  $("play").onclick = viewer.togglePlay;
  $("rewind").onclick = viewer.rewind;
  $("toEnd").onclick = viewer.toEnd;
  $("speed").onchange = function () { viewer.setSpeed(parseFloat(this.value)); };
  $("scrub").oninput = function () { viewer.scrub(this.value / 1000); };
  $("scrub").onchange = viewer.scrubEnd;
  $("showRapid").onchange = function () { viewer.setRapid(this.checked); };
  $("ghost").onchange = function () { viewer.setGhost(this.checked); };
  $("resetView").onclick = viewer.resetView;
  document.addEventListener("keydown", function (e) {
    if (curTab === "draw") { if (editor.onKey(e)) e.preventDefault(); return; }
    if (e.code === "Space" && e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") { e.preventDefault(); viewer.togglePlay(); }
  });

  // ---------- çizim editörü ----------
  var rafForm = 0;
  function edStatus(tx) { $("edinfo").textContent = tx; }
  editor = createHoleEditor($("drawcv"), {
    getC: function () { return C; }, getH: function () { return H; }, setH: function (v) { H = v; },
    getOutline: function () { return outline; }, badHoles: function () { return badMap; }, maxHoles: 20,
    commit: function (label) { render(); schedule(true); edStatus(label); },
    liveUpdate: function () { if (!rafForm) rafForm = requestAnimationFrame(function () { rafForm = 0; render(); }); },
    onSelect: function (i) {
      selHole = i; render();
      $("dupbox").style.opacity = i >= 0 ? 1 : 0.45;
      var c = $("hole_" + i); if (c && c.scrollIntoView) c.scrollIntoView({ block: "nearest" });
    },
    onStatus: edStatus,
    onTool: function (tl) { ["select", "round", "oval", "window"].forEach(function (k) { $("t_" + k).classList.toggle("on", k === tl); }); }
  });
  ["select", "round", "oval", "window"].forEach(function (k) { $("t_" + k).onclick = function () { editor.setTool(k); }; });
  [["s_grid", "grid"], ["s_center", "center"], ["s_edge", "edge"], ["s_align", "align"], ["s_ortho", "ortho"]].forEach(function (p) {
    var e = $(p[0]); e.checked = editor.snap[p[1]]; e.onchange = function () { editor.snap[p[1]] = this.checked; };
  });
  $("s_step").onchange = function () { var v = parseFloat(this.value); if (v > 0) { editor.snap.step = v; editor.draw(); } };
  $("e_undo").onclick = editor.undo; $("e_redo").onclick = editor.redo; $("e_fit").onclick = editor.fit;
  $("e_dup").onclick = function () { editor.duplicate(Math.max(1, Math.round(+$("d_n").value || 1)), +$("d_dx").value || 0, +$("d_dt").value || 0); };
  $("e_del").onclick = function () { editor.onKey({ key: "Delete", target: document.body }); };
  editor.setTool("select");
  new ResizeObserver(function () { editor.draw(); }).observe($("stage"));

  reset();
  $("source").textContent = typeof WIZARD_STATE !== "undefined" ? "Wizard'daki değerlerle açıldı" : "Varsayılan değerlerle açıldı";
  render(); setTab("draw"); viewer.setSpeed(1); compute();
})();
